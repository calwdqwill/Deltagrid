import packageJson from "../../../package.json";

export const dynamic = "force-static";

export function GET() {
  return Response.json({
    app: "deltagrid-frontend",
    version: packageJson.version,
    stage: "frontend",
    read_only: true,
  });
}
