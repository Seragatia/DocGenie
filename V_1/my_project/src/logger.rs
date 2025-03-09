use chrono::Local;
use std::fs::{File, OpenOptions, metadata, rename};
use std::io::{Write, BufWriter};
use std::path::Path;
use std::sync::mpsc::{self, Sender, Receiver};
use std::sync::{Once, ONCE_INIT};
use std::thread;
use std::time::{Duration, Instant};

/// Log levels for our logger.
#[derive(Debug, PartialEq, PartialOrd)]
pub enum LogLevel {
    Debug,
    Info,
    Warning,
    Error,
}

/// A log message struct.
pub struct LogMessage {
    pub timestamp: String,
    pub level: LogLevel,
    pub message: String,
}

/// Configuration for the logger.
pub struct LoggerConfig {
    pub file_path: String,
    pub max_file_size: u64, // in bytes
    pub min_log_level: LogLevel,
    pub log_to_stdout: bool,
}

/// Our Logger structure.
pub struct Logger {
    sender: Sender<LogMessage>,
    config: LoggerConfig,
}

impl Logger {
    /// Initialize the logger with the given configuration.
    /// This function spawns a background thread that processes log messages.
    pub fn init(config: LoggerConfig) -> Logger {
        let (tx, rx): (Sender<LogMessage>, Receiver<LogMessage>) = mpsc::channel();
        let config_clone = config.clone();
        thread::spawn(move || {
            Logger::logging_thread(rx, config_clone);
        });
        Logger { sender: tx, config }
    }

    /// Log a message with a given level.
    pub fn log(&self, level: LogLevel, message: &str) {
        if level < self.config.min_log_level {
            return;
        }
        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
        let log_message = LogMessage {
            timestamp,
            level,
            message: message.to_string(),
        };
        // Ignore send errors (e.g., if the logger thread has crashed)
        let _ = self.sender.send(log_message);
    }

    /// Convenience methods for different log levels.
    pub fn debug(&self, message: &str) {
        self.log(LogLevel::Debug, message);
    }
    pub fn info(&self, message: &str) {
        self.log(LogLevel::Info, message);
    }
    pub fn warn(&self, message: &str) {
        self.log(LogLevel::Warning, message);
    }
    pub fn error(&self, message: &str) {
        self.log(LogLevel::Error, message);
    }

    /// The background logging thread that receives log messages and writes them to file (and optionally stdout).
    fn logging_thread(rx: Receiver<LogMessage>, config: LoggerConfig) {
        let log_path = Path::new(&config.file_path);
        // Ensure the directory exists
        if let Some(parent) = log_path.parent() {
            if let Err(e) = std::fs::create_dir_all(parent) {
                eprintln!("Failed to create log directory: {}", e);
                return;
            }
        }

        // Open the log file with append mode.
        let mut writer = BufWriter::new(
            OpenOptions::new()
                .append(true)
                .create(true)
                .open(log_path)
                .unwrap()
        );

        while let Ok(log_msg) = rx.recv() {
            // Format the log entry
            let entry = format!(
                "[{}] [{:?}] {}\n",
                log_msg.timestamp,
                log_msg.level,
                log_msg.message
            );
            
            // Write to file
            if let Err(e) = writer.write_all(entry.as_bytes()) {
                eprintln!("Failed to write log entry: {}", e);
            }
            writer.flush().unwrap();

            // Optionally write to stdout
            if config.log_to_stdout {
                print!("{}", entry);
            }

            // Check file size and rotate if needed.
            if let Ok(meta) = metadata(log_path) {
                if meta.len() > config.max_file_size {
                    if let Err(e) = Logger::rotate_log(log_path) {
                        eprintln!("Log rotation failed: {}", e);
                    }
                    // Re-open new log file
                    writer = BufWriter::new(
                        OpenOptions::new()
                            .append(true)
                            .create(true)
                            .open(log_path)
                            .unwrap()
                    );
                }
            }
        }
    }

    /// Rotates the log file by renaming the current log file with a timestamp suffix.
    fn rotate_log(log_path: &Path) -> Result<(), Box<dyn std::error::Error>> {
        let timestamp = Local::now().format("%Y%m%d%H%M%S");
        let rotated_filename = format!(
            "{}.{}",
            log_path.to_string_lossy(),
            timestamp
        );
        rename(log_path, rotated_filename)?;
        Ok(())
    }
}

// Implement Clone for LoggerConfig to allow passing it to the logging thread.
impl Clone for LoggerConfig {
    fn clone(&self) -> Self {
        LoggerConfig {
            file_path: self.file_path.clone(),
            max_file_size: self.max_file_size,
            min_log_level: self.min_log_level.clone(),
            log_to_stdout: self.log_to_stdout,
        }
    }
}

// Optionally, implement Clone for LogLevel.
impl Clone for LogLevel {
    fn clone(&self) -> Self {
        match self {
            LogLevel::Debug => LogLevel::Debug,
            LogLevel::Info => LogLevel::Info,
            LogLevel::Warning => LogLevel::Warning,
            LogLevel::Error => LogLevel::Error,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_logger_initialization_and_logging() {
        let config = LoggerConfig {
            file_path: "test.log".to_string(),
            max_file_size: 1024 * 1024, // 1 MB
            min_log_level: LogLevel::Debug,
            log_to_stdout: false,
        };
        let logger = Logger::init(config);
        logger.debug("This is a debug message");
        logger.info("This is an info message");
        logger.warn("This is a warning message");
        logger.error("This is an error message");

        // Ensure log file exists
        assert!(Path::new("test.log").exists());
        
        // Clean up test log file
        let _ = std::fs::remove_file("test.log");
    }
}
