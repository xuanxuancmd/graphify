/**
 * Auth Controller — HTTP controller for authentication endpoints.
 *
 * Exposes auth operations as REST endpoints:
 *   POST /auth/register — register a new user
 *   POST /auth/login    — login and receive JWT token
 *   POST /auth/refresh   — refresh an expired token
 */
import { AuthService } from "./auth.service.ts";

export interface HttpRequest {
  method: string;
  path: string;
  body: Record<string, unknown>;
  headers: Record<string, string>;
}

export interface HttpResponse {
  status: number;
  body: Record<string, unknown>;
}

export class AuthController {
  private readonly authService: AuthService;

  constructor(authService: AuthService) {
    this.authService = authService;
  }

  /**
   * Handle incoming HTTP requests — routes to the appropriate handler.
   */
  handleRequest(req: HttpRequest): HttpResponse {
    const route = `${req.method} ${req.path}`;
    switch (route) {
      case "POST /auth/register":
        return this.handleRegister(req);
      case "POST /auth/login":
        return this.handleLogin(req);
      case "POST /auth/refresh":
        return this.handleRefresh(req);
      default:
        return { status: 404, body: { error: "Not found" } };
    }
  }

  /**
   * POST /auth/register — register a new user account.
   */
  handleRegister(req: HttpRequest): HttpResponse {
    try {
      const { email, password, displayName } = req.body as {
        email: string;
        password: string;
        displayName: string;
      };
      const result = this.authService.register(email, password, displayName);
      return {
        status: 201,
        body: {
          userId: result.user.id,
          email: result.user.email,
          token: result.token,
        },
      };
    } catch (err) {
      return {
        status: 400,
        body: { error: (err as Error).message },
      };
    }
  }

  /**
   * POST /auth/login — authenticate and receive a JWT token.
   */
  handleLogin(req: HttpRequest): HttpResponse {
    try {
      const { email, password } = req.body as {
        email: string;
        password: string;
      };
      const result = this.authService.login(email, password);
      return {
        status: 200,
        body: {
          userId: result.user.id,
          email: result.user.email,
          token: result.token,
        },
      };
    } catch (err) {
      return {
        status: 401,
        body: { error: (err as Error).message },
      };
    }
  }

  /**
   * POST /auth/refresh — refresh an expired JWT token.
   */
  handleRefresh(req: HttpRequest): HttpResponse {
    try {
      const { token } = req.body as { token: string };
      const newToken = this.authService.refreshToken(token);
      return {
        status: 200,
        body: { token: newToken },
      };
    } catch (err) {
      return {
        status: 401,
        body: { error: (err as Error).message },
      };
    }
  }
}
