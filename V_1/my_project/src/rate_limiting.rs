use reqwest::{Client, Response};
use std::time::{Duration, Instant};
use rand::Rng;
use std::error::Error;

#[derive(Clone)]
pub struct RateLimiter {
    max_retries: u32,
    base_delay: u64,  // Base delay in seconds for exponential backoff
    max_delay: u64,   // Maximum delay to prevent excessively long retries
    attempt_counter: u32,
}

impl RateLimiter {
    // Initialize the RateLimiter with base delay, max retries, and max delay
    pub fn new(base_delay: u64, max_retries: u32, max_delay: u64) -> Self {
        RateLimiter {
            base_delay,
            max_retries,
            max_delay,
            attempt_counter: 0,
        }
    }

    // Calculate the exponential backoff delay with jitter
    fn calculate_backoff_delay(&self) -> Duration {
        let base_delay = self.base_delay * 2u64.pow(self.attempt_counter);
        let delay = std::cmp::min(base_delay, self.max_delay);

        // Adding jitter to avoid the thundering herd problem
        let jitter: u64 = rand::thread_rng().gen_range(0..delay / 2);
        Duration::from_secs(delay + jitter)
    }

    // Retry logic with exponential backoff and optional Retry-After header handling
    pub async fn execute_request<F>(&mut self, client: &Client, url: &str, request_fn: F) -> Result<Response, Box<dyn Error>>
    where
        F: FnOnce(&Client, &str) -> reqwest::RequestBuilder,
    {
        let mut retries = 0;
        
        loop {
            // Prepare the request
            let request = request_fn(client, url);
            let response = request.send().await;

            match response {
                Ok(resp) if resp.status().is_success() => {
                    return Ok(resp);
                }
                Ok(resp) if resp.status().as_u16() == 429 => {
                    // Rate limit exceeded (HTTP 429)
                    eprintln!("Rate limit exceeded. Retrying...");
                    retries += 1;

                    if retries >= self.max_retries {
                        return Err(Box::new(std::io::Error::new(std::io::ErrorKind::Other, "Max retry attempts reached")));
                    }

                    // Check if Retry-After header exists (API specific)
                    let retry_after = resp.headers().get("Retry-After");
                    let wait_time = match retry_after {
                        Some(retry_header) => {
                            if let Ok(seconds) = retry_header.to_str()?.parse::<u64>() {
                                Duration::from_secs(seconds)
                            } else {
                                self.calculate_backoff_delay()
                            }
                        }
                        None => self.calculate_backoff_delay(),
                    };

                    eprintln!("Retrying in {:?}", wait_time);
                    tokio::time::sleep(wait_time).await;
                }
                Ok(resp) => {
                    // Other response status code handling
                    eprintln!("Request failed with status: {}", resp.status());
                    return Err(Box::new(std::io::Error::new(std::io::ErrorKind::Other, "Request failed")));
                }
                Err(err) => {
                    // Error in sending request (network issues, timeout, etc.)
                    eprintln!("Request failed: {}", err);
                    return Err(Box::new(err));
                }
            }

            // Exponential backoff: Increase attempt counter
            self.attempt_counter += 1;
        }
    }
}
