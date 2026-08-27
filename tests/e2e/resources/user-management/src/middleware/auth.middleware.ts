/**
 * Auth Middleware — Express-style middleware for JWT authentication.
 *
 * Validates JWT tokens on incoming requests and attaches the decoded
 * user payload to the request for downstream handlers.
 */
import { JwtManager, TokenPayload } from "../auth/jwt.ts";

export interface AuthenticatedRequest {
  method: string;
  path: string;
  headers: Record<string, string>;
  body: Record<string, unknown>;
  user?: TokenPayload;
}

export class AuthMiddleware {
  private readonly jwtManager: JwtManager;
  private readonly publicRoutes: Set<string>;

  constructor(jwtManager: JwtManager, publicRoutes: string[] = []) {
    this.jwtManager = jwtManager;
    this.publicRoutes = new Set(publicRoutes);
  }

  /**
   * Authenticate an incoming request.
   * If the route is public, skip authentication.
   * Otherwise, extract and verify the Bearer token.
   */
  authenticate(req: AuthenticatedRequest): { ok: boolean; error?: string } {
    const route = `${req.method} ${req.path}`;
    if (this.publicRoutes.has(route)) {
      return { ok: true };
    }

    const authHeader = req.headers["authorization"];
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return { ok: false, error: "Missing or invalid Authorization header" };
    }

    const token = authHeader.slice(7);
    try {
      const payload = this.jwtManager.verifyToken(token);
      req.user = payload;
      return { ok: true };
    } catch (err) {
      return { ok: false, error: (err as Error).message };
    }
  }
}
