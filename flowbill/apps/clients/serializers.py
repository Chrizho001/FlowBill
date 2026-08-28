import structlog
from rest_framework import serializers
from .models import Client, CURRENCY_CHOICES

logger = structlog.get_logger(__name__)

VALID_CURRENCIES = [code for code, _ in CURRENCY_CHOICES]
VALID_COUNTRY_CODES = [
    "AF","AL","DZ","AD","AO","AG","AR","AM","AU","AT","AZ","BS","BH","BD",
    "BB","BY","BE","BZ","BJ","BT","BO","BA","BW","BR","BN","BG","BF","BI",
    "CV","KH","CM","CA","CF","TD","CL","CN","CO","KM","CG","CD","CR","HR",
    "CU","CY","CZ","DK","DJ","DM","DO","EC","EG","SV","GQ","ER","EE","SZ",
    "ET","FJ","FI","FR","GA","GM","GE","DE","GH","GR","GD","GT","GN","GW",
    "GY","HT","HN","HU","IS","IN","ID","IR","IQ","IE","IL","IT","JM","JP",
    "JO","KZ","KE","KI","KP","KR","KW","KG","LA","LV","LB","LS","LR","LY",
    "LI","LT","LU","MG","MW","MY","MV","ML","MT","MH","MR","MU","MX","FM",
    "MD","MC","MN","ME","MA","MZ","MM","NA","NR","NP","NL","NZ","NI","NE",
    "NG","NO","OM","PK","PW","PA","PG","PY","PE","PH","PL","PT","QA","RO",
    "RU","RW","KN","LC","VC","WS","SM","ST","SA","SN","RS","SC","SL","SG",
    "SK","SI","SB","SO","ZA","SS","ES","LK","SD","SR","SE","CH","SY","TW",
    "TJ","TZ","TH","TL","TG","TO","TT","TN","TR","TM","TV","UG","UA","AE",
    "GB","US","UY","UZ","VU","VE","VN","YE","ZM","ZW",
]


class ClientSerializer(serializers.ModelSerializer):
    """
    Handles both input validation and output serialization for clients.
    Owner is excluded from input — set by the view from request.user.
    """

    class Meta:
        model = Client
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "company_name",
            "website",
            "address",
            "city",
            "state",
            "country",
            "currency",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_currency(self, value):
        if value not in VALID_CURRENCIES:
            raise serializers.ValidationError(
                f"Invalid currency. Choose from: {', '.join(VALID_CURRENCIES)}"
            )
        return value

    def validate_country(self, value):
        if value and value.upper() not in VALID_COUNTRY_CODES:
            raise serializers.ValidationError(
                "Invalid country code. Use ISO 3166-1 alpha-2 format (e.g. NG, US, GB)."
            )
        return value.upper() if value else value

    def validate_website(self, value):
        if value and not value.startswith(("http://", "https://")):
            raise serializers.ValidationError(
                "Website must be a valid URL starting with http:// or https://"
            )
        return value


class ClientListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views — fewer fields for performance.
    """

    class Meta:
        model = Client
        fields = (
            "id",
            "name",
            "email",
            "company_name",
            "currency",
            "status",
            "created_at",
        )
        read_only_fields = fields