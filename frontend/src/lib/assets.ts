import { existsSync } from "fs";
import path from "path";

/** True when a file exists under /public. Lets owner-supplied images replace the coded fallbacks. */
export function publicFileExists(src: string) {
  return existsSync(path.join(process.cwd(), "public", src.replace(/^\//, "")));
}
