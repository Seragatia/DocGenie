//ssl.rs
use openssl::x509::X509;
use std::fs;
use std::path::Path;
use std::error::Error;
use chrono::{Utc, DateTime};
use openssl::asn1::Asn1TimeRef;

/// Verifies the SSL certificate located at `cert_path` for validity and checks that it matches the provided `domain`.
/// It performs the following steps:
/// 1. Reads and parses the certificate from a PEM file.
/// 2. Checks that the current time falls between the certificate’s "not before" and "not after" times.
/// 3. Validates that the certificate's Common Name (CN) contains the provided domain.
/// (In a production system, you would also check Subject Alternative Names for a more robust match.)
pub fn verify_ssl_certificate(cert_path: &str, domain: &str) -> Result<(), Box<dyn Error>> {
    // Ensure the certificate file exists before proceeding
    if !Path::new(cert_path).exists() {
        return Err(format!("Certificate file does not exist at path: {}", cert_path).into());
    }

    // Read the certificate file
    let cert_data = fs::read(cert_path)?;

    // Parse the certificate from PEM format
    let cert = X509::from_pem(&cert_data)?;

    // Convert certificate validity times to chrono DateTime<Utc>
    let not_before = asn1time_to_chrono(cert.not_before())?;
    let not_after = asn1time_to_chrono(cert.not_after())?;
    let now: DateTime<Utc> = Utc::now();

    // Check if the certificate is currently valid
    if now < not_before {
        return Err(format!("Certificate is not valid yet. Valid from: {}", not_before).into());
    }
    if now > not_after {
        return Err(format!("Certificate has expired. Expired at: {}", not_after).into());
    }

    // Get the Common Name (CN) from the certificate subject
    let subject = cert.subject_name();
    let cn = subject.entries_by_nid(openssl::nid::Nid::COMMONNAME)
        .next()
        .and_then(|entry| entry.data().as_utf8().ok())
        .map(|data| data.to_string())
        .ok_or("Certificate does not contain a Common Name")?;

    // Check if the Common Name contains the expected domain
    if !cn.contains(domain) {
        return Err(format!("Domain mismatch: certificate CN '{}' does not match '{}'", cn, domain).into());
    }

    // If all checks pass, the certificate is considered valid
    Ok(())
}

/// Helper function that converts an OpenSSL ASN1TimeRef into a chrono::DateTime<Utc>.
fn asn1time_to_chrono(time: &Asn1TimeRef) -> Result<DateTime<Utc>, Box<dyn Error>> {
    // Convert the ASN1 time to an RFC 2822 string, then parse it with chrono
    let time_str = time.to_string(); // e.g., "Nov  5 12:34:56 2025 GMT"
    let parsed_time = chrono::DateTime::parse_from_rfc2822(&time_str)?;
    Ok(parsed_time.with_timezone(&Utc))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_verify_ssl_certificate_valid() {
        // Note: Replace "valid_cert.pem" with a path to a valid certificate file for testing.
        let result = verify_ssl_certificate("valid_cert.pem", "example.com");
        // For a valid certificate, result should be Ok(())
        assert!(result.is_ok());
    }

    #[test]
    fn test_verify_ssl_certificate_expired() {
        // Note: Replace "expired_cert.pem" with a path to an expired certificate file for testing.
        let result = verify_ssl_certificate("expired_cert.pem", "example.com");
        // Expect an error because the certificate is expired.
        assert!(result.is_err());
    }

    #[test]
    fn test_verify_ssl_certificate_domain_mismatch() {
        // Note: Replace "valid_cert.pem" with a valid certificate that doesn't match the provided domain.
        let result = verify_ssl_certificate("valid_cert.pem", "wrongdomain.com");
        // Expect an error due to domain mismatch.
        assert!(result.is_err());
    }
}
