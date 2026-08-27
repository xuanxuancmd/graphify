/**
 * Logger — structured logging utility.
 *
 * Provides leveled logging (info, warn, error) with timestamp and context.
 */
export type LogLevel = "info" | "warn" | "error";

export class Logger {
  private readonly context: string;

  constructor(context: string = "app") {
    this.context = context;
  }

  info(message: string, data?: Record<string, unknown>): void {
    this.log("info", message, data);
  }

  warn(message: string, data?: Record<string, unknown>): void {
    this.log("warn", message, data);
  }

  error(message: string, data?: Record<string, unknown>): void {
    this.log("error", message, data);
  }

  private log(level: LogLevel, message: string, data?: Record<string, unknown>): void {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      context: this.context,
      message,
      ...(data ? { data } : {}),
    };
    // Use stderr for logs so stdout stays clean for test output
    process.stderr.write(JSON.stringify(entry) + "\n");
  }
}
