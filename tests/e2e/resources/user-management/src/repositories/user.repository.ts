/**
 * User Repository — data access layer for User aggregate.
 *
 * Provides persistence and query operations for User entities.
 * Email uniqueness is enforced at this layer via the database constraint.
 */
import { User } from "../models/user.ts";

export class UserRepository {
  private users: Map<string, User> = new Map();
  private emailIndex: Map<string, string> = new Map();

  /**
   * Find a user by their ID.
   * Returns undefined if not found.
   */
  findById(id: string): User | undefined {
    return this.users.get(id);
  }

  /**
   * Find a user by their email address.
   * Returns undefined if not found.
   */
  findByEmail(email: string): User | undefined {
    const id = this.emailIndex.get(email);
    if (!id) return undefined;
    return this.users.get(id);
  }

  /**
   * Save a user — inserts or updates.
   * Enforces email uniqueness: throws if another user already has this email.
   */
  save(user: User): void {
    const existingByEmail = this.emailIndex.get(user.email);
    if (existingByEmail && existingByEmail !== user.id) {
      throw new Error("Email already registered by another user");
    }
    this.users.set(user.id, user);
    this.emailIndex.set(user.email, user.id);
  }

  /**
   * Delete a user from the repository (hard delete).
   * Used for cleanup; normal lifecycle uses User.delete() (soft delete).
   */
  delete(id: string): void {
    const user = this.users.get(id);
    if (user) {
      this.emailIndex.delete(user.email);
      this.users.delete(id);
    }
  }

  /**
   * List all users (for admin / pagination).
   */
  findAll(): User[] {
    return Array.from(this.users.values());
  }
}
