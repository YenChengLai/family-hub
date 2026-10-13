import { defineConfig } from "@hey-api/openapi-ts";

// Source of truth: the spec generated from FastAPI (`make generate`).
export default defineConfig({
  input: "../../docs/reference/openapi.json",
  output: { path: "src", clean: true },
});
