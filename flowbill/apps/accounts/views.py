import structlog
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    BusinessProfileSerializer,
    UserDetailsSerializer,
)
from .services import AccountsService

logger = structlog.get_logger(__name__)


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Creates a new user account and dispatches a 6-digit TOTP verification email.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AccountsService.register_user(serializer.validated_data)

        logger.info(
            "auth.register.success",
            user_id=str(user.id),
            email=user.email,
        )

        return Response({
            "status": "success",
            "message": "Account created. Please check your email for the 6-digit verification code.",
            "data": {"email": user.email},
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Authenticates a verified user and returns JWT tokens.
    Access token in response body, refresh token in HttpOnly cookie.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            error_messages = str(errors)
            if "verify your email" in error_messages:
                logger.warning(
                    "auth.login.blocked_unverified",
                    email=request.data.get("email", ""),
                )
                return Response({
                    "status": "error",
                    "code": "EMAIL_NOT_VERIFIED",
                    "message": "Please verify your email before logging in.",
                    "fields": {},
                }, status=status.HTTP_403_FORBIDDEN)

            logger.warning(
                "auth.login.failed",
                email=request.data.get("email", ""),
                reason="invalid_credentials",
            )
            return Response({
                "status": "error",
                "code": "AUTHENTICATION_FAILED",
                "message": "Invalid email or password.",
                "fields": {},
            }, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data["user"]

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        logger.info(
            "auth.login.success",
            user_id=str(user.id),
            email=user.email,
        )

        response = Response({
            "status": "success",
            "message": "Login successful.",
            "data": {
                "access": access_token,
                "user": UserDetailsSerializer(user).data,
            },
        }, status=status.HTTP_200_OK)

        # Set refresh token as HttpOnly cookie
        response.set_cookie(
            key=settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"],
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # 7 days in seconds
        )

        return response


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the refresh token, invalidating the session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"]
        )

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info("auth.logout.success", user_id=str(request.user.id))
            except TokenError:
                logger.warning("auth.logout.invalid_token", user_id=str(request.user.id))
        else:
            logger.warning("auth.logout.no_cookie", user_id=str(request.user.id))

        response = Response({
            "status": "success",
            "message": "Logged out successfully.",
        }, status=status.HTTP_200_OK)

        response.delete_cookie(settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"])
        return response


class VerifyEmailView(APIView):
    """
    POST /api/v1/auth/verify-email/
    Verifies user email using the 6-digit OTP.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_verify"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = AccountsService.verify_email(email=email, otp=otp)
        except ValueError as e:
            logger.warning(
                "auth.verify_email.failed",
                email=email,
                reason=str(e),
            )
            return Response({
                "status": "error",
                "code": "VERIFICATION_FAILED",
                "message": str(e),
                "fields": {},
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info("auth.verify_email.success", user_id=str(user.id), email=user.email)

        return Response({
            "status": "success",
            "message": "Email verified successfully. You can now log in.",
            "data": {"email": user.email},
        }, status=status.HTTP_200_OK)


class ResendVerificationView(APIView):
    """
    POST /api/v1/auth/resend-verification/
    Resends a 6-digit verification code with a 60-second cooldown.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_resend"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            AccountsService.resend_verification_otp(email)
        except ValueError as e:
            logger.warning(
                "auth.resend_verification.failed",
                email=email,
                reason=str(e),
            )
            return Response({
                "status": "error",
                "code": "RESEND_FAILED",
                "message": str(e),
                "fields": {},
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info("auth.resend_verification.success", email=email)

        return Response({
            "status": "success",
            "message": "A new verification code has been sent to your email.",
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    POST /api/v1/auth/password-reset/
    Requests a password reset code.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_reset_request"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        AccountsService.request_password_reset(email)

        logger.info("auth.password_reset.requested", email=email)

        return Response({
            "status": "success",
            "message": "If an account exists with this email, a password reset code has been sent.",
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    POST /api/v1/auth/password-reset/confirm/
    Verifies OTP and resets the password.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_reset_confirm"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            AccountsService.confirm_password_reset(
                email=email,
                otp=serializer.validated_data["otp"],
                new_password=serializer.validated_data["password"],
            )
        except ValueError as e:
            logger.warning(
                "auth.password_reset_confirm.failed",
                email=email,
                reason=str(e),
            )
            return Response({
                "status": "error",
                "code": "PASSWORD_RESET_FAILED",
                "message": str(e),
                "fields": {},
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info("auth.password_reset_confirm.success", email=email)

        return Response({
            "status": "success",
            "message": "Password reset successful. You can now log in with your new password.",
        }, status=status.HTTP_200_OK)


class BusinessProfileView(APIView):
    """
    GET /api/v1/auth/profile/
    PUT / PATCH /api/v1/auth/profile/
    Manage the authenticated user's business profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = AccountsService.get_or_create_profile(request.user)
        logger.info("auth.profile.retrieved", user_id=str(request.user.id), profile_id=str(profile.id))
        return Response({
            "status": "success",
            "data": BusinessProfileSerializer(profile).data,
        }, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial=True):
        serializer = BusinessProfileSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        profile = AccountsService.update_profile(request.user, serializer.validated_data)

        logger.info(
            "auth.profile.updated",
            user_id=str(request.user.id),
            profile_id=str(profile.id),
            fields_changed=list(serializer.validated_data.keys()),
        )

        return Response({
            "status": "success",
            "message": "Business profile updated successfully.",
            "data": BusinessProfileSerializer(profile).data,
        }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """
    POST /api/v1/auth/refresh/
    Issues a new access token using the refresh token from the HttpOnly cookie.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_refresh"

    def post(self, request):
        refresh_token = request.COOKIES.get(
            settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"]
        )

        if not refresh_token:
            logger.warning("auth.refresh.missing_cookie")
            return Response({
                "status": "error",
                "code": "REFRESH_TOKEN_MISSING",
                "message": "No refresh token provided.",
                "fields": {},
            }, status=status.HTTP_401_UNAUTHORIZED)

        try:
            from django.contrib.auth import get_user_model
            from rest_framework_simplejwt.settings import api_settings

            User = get_user_model()
            token = RefreshToken(refresh_token)

            if request.user and request.user.is_authenticated:
                user = request.user
            else:
                user_id = token.payload.get(api_settings.USER_ID_CLAIM)
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                except (User.DoesNotExist, ValueError, TypeError):
                    raise TokenError("User not found or inactive.")

            new_refresh = RefreshToken.for_user(user)
            new_access_token = str(new_refresh.access_token)

            # Blacklist old refresh token only after the replacement is minted
            token.blacklist()

            response = Response({
                "status": "success",
                "data": {"access": new_access_token},
            }, status=status.HTTP_200_OK)

            response.set_cookie(
                key=settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"],
                value=str(new_refresh),
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
            )

            logger.info("auth.refresh.success", user_id=str(user.id))
            return response

        except TokenError:
            logger.warning("auth.refresh.invalid_token")
            return Response({
                "status": "error",
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Refresh token is invalid or expired.",
                "fields": {},
            }, status=status.HTTP_401_UNAUTHORIZED)