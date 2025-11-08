const API_BASE_URL = "http://127.0.0.1:8000/api";

/**
 * Start the Google OAuth flow.
 * Redirects the user to the backend endpoint, which will
 * send them to Google's authentication page.
 */
export function signInWithGoogle() {
  window.location.href = `${API_BASE_URL}/google/auth`;
}
