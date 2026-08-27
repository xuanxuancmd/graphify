/**
 * Application entry point.
 *
 * Exports the buildApp function for testing and programmatic use.
 * In production, this would start an HTTP server.
 */
export { buildApp, defaultConfig, AppConfig } from "./config.ts";
export { User, Profile, UserStatus } from "./models/user.ts";
export { UserRepository } from "./repositories/user.repository.ts";
export { PasswordHasher } from "./auth/password.ts";
export { JwtManager, TokenPayload } from "./auth/jwt.ts";
export { AuthService, AuthResult } from "./auth/auth.service.ts";
export { AuthController } from "./auth/auth.controller.ts";
export { UserService } from "./services/user.service.ts";
export { AuthMiddleware } from "./middleware/auth.middleware.ts";
export { Logger, LogLevel } from "./utils/logger.ts";
