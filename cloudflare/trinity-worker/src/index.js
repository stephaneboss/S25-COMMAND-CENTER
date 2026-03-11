const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
]);

const RETRYABLE_STATUS_CODES = new Set([502, 503, 504]);
const ALLOWED_PATH_PREFIXES = ["/api/", "/health", "/favicon.ico"];
const BUSINESS_PREFIX = "/api/business";

const BUSINESS_REGISTRIES = {
  clients: {
    title: "Clients registry MVP",
    description: "Registre minimum pour nouveaux clients, sans reprendre l'ancien hiver.",
    records: [
      "client_id",
      "organization_name",
      "contact_name",
      "contact_channel",
      "service_address",
      "service_type",
      "account_status",
    ],
    workflows: [
      "create_client",
      "activate_services",
      "attach_quote",
      "attach_job",
      "invoice_and_collect",
    ],
  },
  jobs: {
    title: "Jobs registry MVP",
    description: "Registre des interventions terrain en execution.",
    records: [
      "job_id",
      "client_id",
      "service_type",
      "assigned_team",
      "equipment_required",
      "scheduled_window",
      "job_status",
    ],
    workflows: [
      "open_job",
      "dispatch_team",
      "track_execution",
      "capture_report",
      "close_job",
    ],
  },
  quotes_invoices: {
    title: "Quotes and invoices registry MVP",
    description: "Registre devis, factures et suivi paiements.",
    records: [
      "quote_id",
      "invoice_id",
      "client_id",
      "job_id",
      "amount",
      "payment_status",
      "billing_stage",
    ],
    workflows: [
      "issue_quote",
      "approve_quote",
      "issue_invoice",
      "track_payment",
      "report_margin",
    ],
  },
};

const BUSINESS_ONBOARDING = {
  title: "Business onboarding chain",
  summary: "Tout nouvel acteur doit entrer par une chaine stricte: identite, role, services, acces.",
  tracks: {
    client: [
      "create_client_identity",
      "link_to_organization",
      "activate_service_contract",
      "issue_portal_access",
      "attach_quote_and_job",
    ],
    employee: [
      "create_employee_identity",
      "assign_role",
      "enable_staff_portal",
      "attach_shift_and_dispatch_scope",
      "issue_secure_credentials",
    ],
    vendor: [
      "create_vendor_identity",
      "link_vendor_org",
      "enable_vendor_portal",
      "attach_purchase_scope",
      "issue_document_access",
    ],
  },
};

const BUSINESS_REGISTRY_MAP = {
  title: "Smajor business registry map",
  source_of_truth: "api.smajor.org facade + S25 governance",
  registries: [
    { key: "clients", path: `${BUSINESS_PREFIX}/clients`, purpose: "Customer and account intake" },
    { key: "jobs", path: `${BUSINESS_PREFIX}/jobs`, purpose: "Field operations and execution" },
    { key: "quotes_invoices", path: `${BUSINESS_PREFIX}/quotes-invoices`, purpose: "Commercial and billing flow" },
    { key: "onboarding", path: `${BUSINESS_PREFIX}/onboarding`, purpose: "Strict actor activation chain" },
  ],
};

function buildTargetUrl(requestUrl, originBase) {
  const incoming = new URL(requestUrl);
  const origin = new URL(originBase);
  origin.pathname = incoming.pathname;
  origin.search = incoming.search;
  return origin;
}

function businessResponse(requestId, pathname, payload, status = 200) {
  return jsonResponse(
    {
      ok: true,
      service: "trinity-s25-proxy",
      request_id: requestId,
      pathname,
      ...payload,
    },
    { status },
  );
}

function handleBusinessRequest(pathname, requestId) {
  if (pathname === `${BUSINESS_PREFIX}` || pathname === `${BUSINESS_PREFIX}/`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRY_MAP);
  }
  if (pathname === `${BUSINESS_PREFIX}/registry-map`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRY_MAP);
  }
  if (pathname === `${BUSINESS_PREFIX}/clients`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRIES.clients);
  }
  if (pathname === `${BUSINESS_PREFIX}/jobs`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRIES.jobs);
  }
  if (pathname === `${BUSINESS_PREFIX}/quotes-invoices`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRIES.quotes_invoices);
  }
  if (pathname === `${BUSINESS_PREFIX}/onboarding`) {
    return businessResponse(requestId, pathname, BUSINESS_ONBOARDING);
  }
  return null;
}

function shouldProxyPath(pathname) {
  return ALLOWED_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function jsonResponse(payload, init = {}) {
  const headers = new Headers(init.headers || {});
  headers.set("content-type", "application/json; charset=utf-8");
  headers.set("cache-control", "no-store");
  headers.set("access-control-allow-origin", "*");
  headers.set("access-control-allow-methods", "GET,HEAD,POST,OPTIONS");
  headers.set("access-control-allow-headers", "*");
  return new Response(JSON.stringify(payload, null, 2), {
    ...init,
    headers,
  });
}

function copyRequestHeaders(headers, requestId, env, clientIp) {
  const out = new Headers();
  for (const [key, value] of headers.entries()) {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      out.set(key, value);
    }
  }
  if (env.ORIGIN_HOST_HEADER) {
    out.set("host", env.ORIGIN_HOST_HEADER);
  }
  if (env.S25_SHARED_SECRET) {
    out.set("x-s25-secret", env.S25_SHARED_SECRET);
  }
  out.set("x-trinity-request-id", requestId);
  if (clientIp) {
    out.set("x-forwarded-for", clientIp);
    out.set("cf-connecting-ip", clientIp);
  }
  return out;
}

function copyResponseHeaders(headers, requestId) {
  const out = new Headers();
  for (const [key, value] of headers.entries()) {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      out.set(key, value);
    }
  }
  out.set("cache-control", "no-store");
  out.set("access-control-allow-origin", "*");
  out.set("access-control-allow-methods", "GET,HEAD,POST,OPTIONS");
  out.set("access-control-allow-headers", "*");
  out.set("x-trinity-request-id", requestId);
  out.set("x-trinity-proxy", "trinity-s25-proxy");
  return out;
}

function buildProxyMeta(env, requestId, targetUrl) {
  return {
    ok: true,
    service: "trinity-s25-proxy",
    request_id: requestId,
    target_origin: new URL(env.ORIGIN_BASE).origin,
    target_url: targetUrl.toString(),
    timeout_ms: Number(env.PROXY_TIMEOUT_MS || 15000),
    retries: Number(env.PROXY_RETRIES || 1),
    shared_secret_configured: Boolean(env.S25_SHARED_SECRET),
  };
}

async function fetchWithPolicy(target, request, env, requestId) {
  const timeoutMs = Number(env.PROXY_TIMEOUT_MS || 15000);
  const maxRetries = Math.max(0, Number(env.PROXY_RETRIES || 1));
  const clientIp = request.headers.get("cf-connecting-ip") || "";
  const method = request.method.toUpperCase();
  const canRetry = method === "GET" || method === "HEAD";
  const bodyBuffer =
    method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  let attempt = 0;
  let lastError = null;

  while (attempt <= maxRetries) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort("proxy-timeout"), timeoutMs);
    try {
      const upstream = await fetch(target, {
        method,
        headers: copyRequestHeaders(request.headers, requestId, env, clientIp),
        redirect: "follow",
        body: bodyBuffer,
        signal: controller.signal,
      });

      if (!canRetry || !RETRYABLE_STATUS_CODES.has(upstream.status) || attempt === maxRetries) {
        return upstream;
      }
      lastError = new Error(`upstream-status-${upstream.status}`);
    } catch (error) {
      lastError = error;
      if (!canRetry || attempt === maxRetries) {
        throw error;
      }
    } finally {
      clearTimeout(timeout);
    }

    attempt += 1;
  }

  throw lastError || new Error("proxy-failed");
}

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    const requestId = crypto.randomUUID();

    if (request.method === "OPTIONS") {
      return jsonResponse(
        { ok: true, request_id: requestId, methods: ["GET", "HEAD", "POST", "OPTIONS"] },
        { status: 204 }
      );
    }

    if (incoming.pathname === "/health" || incoming.pathname === "/api/health") {
      return jsonResponse(buildProxyMeta(env, requestId, buildTargetUrl(request.url, env.ORIGIN_BASE)));
    }

    const businessRoute = handleBusinessRequest(incoming.pathname, requestId);
    if (businessRoute) {
      return businessRoute;
    }

    if (!shouldProxyPath(incoming.pathname)) {
      return jsonResponse(
        {
          ok: false,
          error: "path_not_allowed",
          request_id: requestId,
          pathname: incoming.pathname,
        },
        { status: 404 }
      );
    }

    const target = buildTargetUrl(request.url, env.ORIGIN_BASE);
    try {
      const upstream = await fetchWithPolicy(target, request, env, requestId);
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: copyResponseHeaders(upstream.headers, requestId),
      });
    } catch (error) {
      return jsonResponse(
        {
          ok: false,
          error: "upstream_unreachable",
          request_id: requestId,
          detail: String(error),
          target: target.toString(),
        },
        { status: 502 }
      );
    }
  },
};
