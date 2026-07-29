/**
 * Proxy https://mansejin.com/autotrade* -> Oracle desk
 * Origin uses DNS-only hostname (Workers cannot fetch bare IPs).
 */
const ORIGIN = "https://autotrade-origin.mansejin.com";
const ALLOWED_METHODS = new Set(["GET", "HEAD", "POST"]);

function isSafePath(pathname) {
  if (!pathname.startsWith("/autotrade")) return false;
  if (pathname.includes("..") || pathname.includes("//")) return false;
  if (pathname.includes("%2e") || pathname.includes("%2E")) return false;
  return true;
}

export default {
  async fetch(request) {
    const incoming = new URL(request.url);
    if (!isSafePath(incoming.pathname)) {
      return new Response("Not Found", { status: 404 });
    }
    if (!ALLOWED_METHODS.has(request.method)) {
      return new Response("Method Not Allowed", { status: 405 });
    }

    if (incoming.pathname === "/autotrade") {
      incoming.pathname = "/autotrade/";
      return Response.redirect(incoming.toString(), 302);
    }

    const target = new URL(incoming.pathname + incoming.search, ORIGIN);
    const headers = new Headers();
    // Forward only what the origin needs — drop hop-by-hop / sensitive extras.
    const allow = [
      "accept",
      "accept-language",
      "content-type",
      "cookie",
      "user-agent",
      "authorization",
    ];
    for (const name of allow) {
      const v = request.headers.get(name);
      if (v) headers.set(name, v);
    }
    headers.set("Host", "autotrade-origin.mansejin.com");
    headers.set("X-Forwarded-Host", incoming.host);
    headers.set("X-Forwarded-Proto", "https");
    headers.set("X-Forwarded-Prefix", "/autotrade");
    const clientIp = request.headers.get("cf-connecting-ip");
    if (clientIp) {
      headers.set("X-Forwarded-For", clientIp);
      headers.set("X-Real-IP", clientIp);
    }

    const init = {
      method: request.method,
      headers,
      redirect: "manual",
    };
    if (request.method !== "GET" && request.method !== "HEAD") {
      init.body = request.body;
      // @ts-expect-error duplex for streaming body
      init.duplex = "half";
    }

    const upstream = await fetch(target.toString(), init);
    const outHeaders = new Headers(upstream.headers);
    outHeaders.delete("transfer-encoding");
    outHeaders.delete("connection");
    outHeaders.set("X-Content-Type-Options", "nosniff");
    outHeaders.set("X-Frame-Options", "DENY");
    outHeaders.set("Referrer-Policy", "no-referrer");
    const loc = outHeaders.get("Location");
    if (loc) {
      try {
        const u = new URL(loc, ORIGIN);
        if (u.origin === new URL(ORIGIN).origin || loc.startsWith("/")) {
          const path = loc.startsWith("http") ? u.pathname + u.search : loc;
          outHeaders.set("Location", new URL(path, incoming.origin).toString());
        }
      } catch {
        /* keep */
      }
    }

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: outHeaders,
    });
  },
};
