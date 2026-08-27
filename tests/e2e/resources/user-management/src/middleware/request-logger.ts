/**
 * Request Logger — middleware-scoped logging for HTTP requests.
 *
 * This is intentionally a SECOND class named ``Logger`` (the first lives in
 * ``src/utils/logger.ts``). It exists as an E2E fixture for the DDD
 * extractor's multi-match confidence logic (Gap-6): when a DDD doc anchors
 * to ``Logger`` by SimpleName, both classes match → all edges get
 * ``confidence="AMBIGUOUS"`` + ``confidence_score=0.3``.
 */
export class Logger {
  private readonly requestId: string;

  constructor(requestId: string) {
    this.requestId = requestId;
  }

  logRequest(method: string, path: string): void {
    process.stderr.write(
      JSON.stringify({ requestId: this.requestId, method, path }) + "\n"
    );
  }
}
