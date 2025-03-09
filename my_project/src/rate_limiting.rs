use reqwest::{Client, Response};
use std::time::Duration;
use rand::Rng;
use std::error::Error;
use log::{debug, warn, error};

/// A simple rate limiter that supports exponential backoff with jitter.
#[derive(Clone)]
pub struct RateLimiter {
    max_retries: u32,
    base_delay: u64,  // Base delay in seconds for exponential backoff
    max_delay: u64,   // Maximum delay to cap the backoff
    attempt_counter: u32,
}

impl RateLimiter {
    /// Creates a new RateLimiter.
    ///
    /// # Arguments
    ///
    /// * `base_delay` - The initial delay in seconds.
    /// * `max_retries` - Maximum number of retry attempts.
    /// * `max_delay` - Maximum delay in seconds.
    pub fn new(base_delay: u64, max_retries: u32, max_delay: u64) -> Self {
        RateLimiter {
            base_delay,
            max_retries,
            max_delay,
            attempt_counter: 0,
        }
    }

    /// Calculates the backoff delay using exponential backoff and a random jitter.
    /// The delay doubles for each retry (capped by `max_delay`), and a random jitter
    /// between 0 and half the delay (inclusive) is added.
    fn calculate_backoff_delay(&self) -> Duration {
        // Calculate exponential delay: base_delay * 2^(attempt_counter)
        let exp_delay = self.base_delay.saturating_mul(2u64.pow(self.attempt_counter));
        // Cap the delay to max_delay.
        let delay = std::cmp::min(exp_delay, self.max_delay);
        // Generate jitter between 0 and delay/2.
        let jitter: u64 = rand::thread_rng().gen_range(0..=(delay / 2));
        Duration::from_secs(delay) + Duration::from_secs(jitter)
    }

    /// Executes the provided asynchronous request function with rate limiting.
    ///
    /// The `request_fn` is a closure that creates a reqwest `RequestBuilder` and will be
    /// invoked on every retry.
    ///
    /// # Arguments
    ///
    /// * `client` - The reqwest Client.
    /// * `url` - The URL for the request.
    /// * `request_fn` - A closure that takes a client and URL and returns a RequestBuilder.
    ///
    /// # Returns
    ///
    /// * On success, returns the successful Response.
    /// * On failure after all retries, returns an error.
    pub async fn execute_request<F>(
        &mut self,
        client: &Client,
        url: &str,
        mut request_fn: F,
    ) -> Result<Response, Box<dyn Error>>
    where
        F: FnMut(&Client, &str) -> reqwest::RequestBuilder,
    {
        self.attempt_counter = 0; // Reset the counter for each new request
        let mut retries = 0;

        loop {
            debug!("Sending request attempt {} to: {}", retries + 1, url);

            // Create and send the request.
            let request = request_fn(client, url);
            let response = request.send().await;

            match response {
                Ok(resp) if resp.status().is_success() => {
                    // Reset attempt counter on success.
                    self.attempt_counter = 0;
                    debug!("Successful response with status {}", resp.status());
                    return Ok(resp);
                }
                Ok(resp) if resp.status().as_u16() == 429 => {
                    // Handle rate limiting.
                    warn!("Received HTTP 429 (rate limit) response. Retrying...");
                    retries += 1;
                    self.attempt_counter += 1;

                    if retries >= self.max_retries {
                        error!("Max retry attempts reached after HTTP 429.");
                        return Err(Box::new(std::io::Error::new(
                            std::io::ErrorKind::Other,
                            "Max retry attempts reached after rate limiting",
                        )));
                    }

                    // Check if the server provides a Retry-After header.
                    let wait_time = if let Some(retry_header) = resp.headers().get("Retry-After") {
                        match retry_header.to_str()?.parse::<u64>() {
                            Ok(seconds) => Duration::from_secs(seconds),
                            Err(_) => self.calculate_backoff_delay(),
                        }
                    } else {
                        self.calculate_backoff_delay()
                    };

                    warn!("Waiting {:?} before retrying...", wait_time);
                    tokio::time::sleep(wait_time).await;
                }
                Ok(resp) => {
                    // For other non-successful responses.
                    error!("Request failed with status: {}", resp.status());
                    return Err(Box::new(std::io::Error::new(
                        std::io::ErrorKind::Other,
                        format!("Request failed with HTTP status {}", resp.status()),
                    )));
                }
                Err(err) => {
                    // Handle network or other errors.
                    error!("Request error: {}", err);
                    return Err(Box::new(err));
                }
            }
        }
    }
}
