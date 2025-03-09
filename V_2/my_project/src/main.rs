use std::ffi::{CString, CStr};
use std::os::raw::c_char;
use std::error::Error;
use my_project::download::{download_file, pause_download, resume_download};
use my_project::progress::track_progress;
use my_project::logger;  // Ensure logger::log_error is defined in logger.rs
use my_project::auth;    // Ensure auth::authenticate_platform is defined in auth.rs
use my_project::ssl;     // Ensure ssl::verify_ssl_certificate is defined in ssl.rs

// Main entry function - typically not needed for FFI, but good for standalone use.
fn main() {
    // Example: Start a download
    let url = "https://example.com/file.zip";
    match download_file(url) {
        Ok(_) => println!("Download started successfully!"),
        Err(e) => println!("Failed to start download: {}", e),
    }
}

// FFI interface function to start a download from Python.
#[no_mangle]
pub extern "C" fn download_file_ffi(url: *const c_char) -> *mut c_char {
    if url.is_null() {
        return CString::new("Invalid URL pointer").unwrap().into_raw();
    }
    unsafe {
        let c_str = match CStr::from_ptr(url).to_str() {
            Ok(s) => s,
            Err(_) => return CString::new("Failed to convert URL to string").unwrap().into_raw(),
        };

        // Call Rust download logic.
        match download_file(c_str) {
            Ok(_) => CString::new("Download started successfully").unwrap().into_raw(),
            Err(e) => CString::new(format!("Download failed: {}", e)).unwrap().into_raw(),
        }
    }
}

// FFI interface function to track download progress.
#[no_mangle]
pub extern "C" fn track_progress_ffi(total_size: u64, downloaded: u64) -> *mut c_char {
    // Use the progress tracking function.
    let progress_str = track_progress(total_size, downloaded);
    CString::new(progress_str).unwrap().into_raw()
}

// FFI interface function to pause a download.
#[no_mangle]
pub extern "C" fn pause_download_ffi() -> *mut c_char {
    match pause_download() {
        Ok(_) => CString::new("Download paused").unwrap().into_raw(),
        Err(e) => CString::new(format!("Failed to pause: {}", e)).unwrap().into_raw(),
    }
}

// FFI interface function to resume a paused download.
#[no_mangle]
pub extern "C" fn resume_download_ffi(url: *const c_char) -> *mut c_char {
    if url.is_null() {
        return CString::new("Invalid URL pointer").unwrap().into_raw();
    }
    unsafe {
        let c_str = match CStr::from_ptr(url).to_str() {
            Ok(s) => s,
            Err(_) => return CString::new("Failed to convert URL to string").unwrap().into_raw(),
        };

        match resume_download(c_str) {
            Ok(_) => CString::new("Download resumed").unwrap().into_raw(),
            Err(e) => CString::new(format!("Failed to resume: {}", e)).unwrap().into_raw(),
        }
    }
}

// FFI interface function to handle errors (useful for debugging).
#[no_mangle]
pub extern "C" fn handle_error_ffi(error_message: *const c_char) -> *mut c_char {
    if error_message.is_null() {
        return CString::new("No error message provided").unwrap().into_raw();
    }
    unsafe {
        let c_str = match CStr::from_ptr(error_message).to_str() {
            Ok(s) => s,
            Err(_) => "Error converting error message",
        };
        logger::log_error(c_str);
        CString::new("Error handled successfully").unwrap().into_raw()
    }
}

// FFI interface function to handle authentication.
#[no_mangle]
pub extern "C" fn authenticate_ffi(api_key: *const c_char) -> *mut c_char {
    if api_key.is_null() {
        return CString::new("Invalid API key pointer").unwrap().into_raw();
    }
    unsafe {
        let c_str = match CStr::from_ptr(api_key).to_str() {
            Ok(s) => s,
            Err(_) => return CString::new("Failed to convert API key to string").unwrap().into_raw(),
        };
        match auth::authenticate_platform(c_str) {
            Ok(_) => CString::new("Authentication successful").unwrap().into_raw(),
            Err(e) => CString::new(format!("Authentication failed: {}", e)).unwrap().into_raw(),
        }
    }
}

// FFI interface function to handle SSL verification.
#[no_mangle]
pub extern "C" fn verify_ssl_ffi(cert_path: *const c_char) -> *mut c_char {
    if cert_path.is_null() {
        return CString::new("Invalid certificate path pointer").unwrap().into_raw();
    }
    unsafe {
        let c_str = match CStr::from_ptr(cert_path).to_str() {
            Ok(s) => s,
            Err(_) => return CString::new("Failed to convert certificate path to string").unwrap().into_raw(),
        };
        match ssl::verify_ssl_certificate(c_str, "example.com") {
            Ok(_) => CString::new("SSL certificate verified successfully").unwrap().into_raw(),
            Err(e) => CString::new(format!("SSL certificate verification failed: {}", e)).unwrap().into_raw(),
        }
    }
}
