/**
 * Application configuration.
 *
 * Centralizes all configuration values with sensible test defaults.
 */
export interface AppConfig {
  jwtSecret: string;
  jwtExpiresInSec: number;
  bcryptSaltRounds: number;
  publicRoutes: string[];
}

export const defaultConfig: AppConfig = {
  jwtSecret: "test-secret-key",
  jwtExpiresInSec: 3600,
  bcryptSaltRounds: 10,
  publicRoutes: [
    "POST /auth/register",
    "POST /auth/login",
    "POST /auth/refresh",
  ],
};

/**
 * Build the application dependency graph.
 * Wires together repository, services, controllers, and middleware.
 */
export function buildApp() {
  const { UserRepository } = require("./repositories/user.repository.ts");
  const { PasswordHasher } = require("./auth/password.ts");
  const { JwtManager } = require("./auth/jwt.ts");
  const { AuthService } = require("./auth/auth.service.ts");
  const { AuthController } = require("./auth/auth.controller.ts");
  const { UserService } = require("./services/user.service.ts");
  const { AuthMiddleware } = require("./middleware/auth.middleware.ts");
  const { Logger } = require("./utils/logger.ts");

  const logger = new Logger("app");
  const userRepo = new UserRepository();
  const passwordHasher = new PasswordHasher(defaultConfig.bcryptSaltRounds);
  const jwtManager = new JwtManager(
    defaultConfig.jwtSecret,
    defaultConfig.jwtExpiresInSec,
  );
  const authService = new AuthService(userRepo, passwordHasher, jwtManager);
  const userService = new UserService(userRepo);
  const authController = new AuthController(authService);
  const authMiddleware = new AuthMiddleware(
    jwtManager,
    defaultConfig.publicRoutes,
  );

  return {
    logger,
    userRepo,
    passwordHasher,
    jwtManager,
    authService,
    userService,
    authController,
    authMiddleware,
  };
}
