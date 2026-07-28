/**
 * Proxy https://mansejin.com/autotrade* -> Oracle desk
 * Origin uses DNS-only hostname (Workers cannot fetch bare IPs).
 */
const ORIGIN = "http://autotrade-origin.mansejin.com";

export default {
  async fetch(request) {
    const incoming = new URL(request.url);
    if (!incoming.pathname.startsWith("/autotrade")) {
      return new Response("Not Found", { status: 404 });
    }

    if (incoming.pathname === "/autotrade") {
      incoming.pathname = "/autotrade/";
      return Response.redirect(incoming.toString(), 302);
    }

    const target = new URL(incoming.pathname + incoming.search, ORIGIN);
    const headers = new Headers(request.headers);
    headers.set("Host", "autotrade-origin.mansejin.com");
    headers.set("X-Forwarded-Host", incoming.host);
    headers.set("X-Forwarded-Proto", "https");
    headers.set("X-Forwarded-Prefix", "/autotrade");

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
