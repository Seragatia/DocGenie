use std::fs::OpenOptions;
use std::io::{Write, Error as IoError};
use chrono::Utc;
use log::{error, debug};
use std::backtrace::Backtrace;

/// The log file path used for backend error logging.
const LOG_FILE_PATH: &str = "rust_backend.log";

/// Writes an error message to the log file with a human‑readable UTC timestamp and a backtrace,
/// and also logs the error using the standard log framework.
///
/// **Note:** This function is not thread‑safe. If multiple threads call it concurrently,
/// consider wrapping file writes in a Mutex or using an asynchronous logger.
///
/// # Example
/// ```ignore
/// log_error_with_backtrace("Something went wrong while downloading...");
/// ```
pub fn log_error_with_backtrace(message: &str) -> Result<(), IoError> {
    // Log the error using the standard log framework.
    error!("{}", message);

    // Capture the current backtrace.
    let backtrace = Backtrace::capture();

    // Get the current UTC timestamp as a formatted string.
    let timestamp = Utc::now().format("%Y-%m-%d %H:%M:%S");

    // Format the log line with backtrace.
    let log_line = format!(
        "[{}] ERROR: {}\nBacktrace:\n{:?}\n",
        timestamp, message, backtrace
    );

    // Open (or create) the log file in append mode.
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(LOG_FILE_PATH)?;
    // Write the log line and flush.
    file.write_all(log_line.as_bytes())?;
    file.flush()?;

    debug!("Wrote error message with backtrace to '{}' successfully.", LOG_FILE_PATH);
    Ok(())
}
