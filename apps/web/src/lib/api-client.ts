const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;

    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data.access_token as string;
  } catch {
    return null;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets multipart boundary)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 with token refresh
  if (res.status === 401 && retry) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      return request<T>(endpoint, options, false);
    }
    // Refresh failed — clear auth state and redirect to login
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    
    // Dispatch a custom event so auth store can update and show toast
    if (typeof window !== "undefined") {
      const event = new CustomEvent("session-expired", {
        detail: "Session expired. Please sign in again.",
      });
      window.dispatchEvent(event);
      
      // Small delay to allow toast to render before navigation
      setTimeout(() => {
        window.location.href = "/login";
      }, 100);
    }
    
    throw new ApiError(401, "Session expired");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, detail);
  }

  // Handle 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

// Upload with progress tracking using XMLHttpRequest
function uploadWithProgress<T>(
  endpoint: string,
  formData: FormData,
  onProgress?: (progress: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const token = getAccessToken();

    xhr.open("POST", `${API_URL}${endpoint}`);

    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          onProgress(percentComplete);
        }
      });
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response as T);
        } catch {
          reject(new Error("Failed to parse response"));
        }
      } else if (xhr.status === 401) {
        // Handle token refresh
        refreshAccessToken().then((newToken) => {
          if (newToken) {
            // Retry with new token
            const retryXhr = new XMLHttpRequest();
            retryXhr.open("POST", `${API_URL}${endpoint}`);
            retryXhr.setRequestHeader("Authorization", `Bearer ${newToken}`);
            retryXhr.onload = () => {
              if (retryXhr.status >= 200 && retryXhr.status < 300) {
                try {
                  resolve(JSON.parse(retryXhr.responseText) as T);
                } catch {
                  reject(new Error("Failed to parse response"));
                }
              } else {
                reject(new ApiError(retryXhr.status, retryXhr.statusText));
              }
            };
            retryXhr.onerror = () => reject(new Error("Network error"));
            retryXhr.send(formData);
          } else {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            localStorage.removeItem("user");
            window.location.href = "/login";
            reject(new ApiError(401, "Session expired"));
          }
        });
      } else {
        let detail = xhr.statusText;
        try {
          const body = JSON.parse(xhr.responseText);
          detail = body.detail || detail;
        } catch {
          // ignore parse error
        }
        reject(new ApiError(xhr.status, detail));
      }
    };

    xhr.onerror = () => reject(new Error("Network error"));
    xhr.ontimeout = () => reject(new Error("Request timeout"));

    xhr.send(formData);
  });
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  upload: <T>(endpoint: string, formData: FormData, onProgress?: (progress: number) => void) =>
    uploadWithProgress<T>(endpoint, formData, onProgress),

  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "PUT",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  patch: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),
};

export { ApiError };
