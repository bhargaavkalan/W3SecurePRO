const API = "https://w3securepro.onrender.com";

/* =========================
   TOKEN HELPERS
========================= */

function token() {
  return localStorage.getItem("w3token");
}
function setToken(t) {
  localStorage.setItem("w3token", t);
}
function logout() {
  localStorage.removeItem("w3token");
  window.location.href = "index.html";
}

/* =========================
   API REQUEST
========================= */

async function api(path, method="GET", body=null) {
  const headers = { "Content-Type": "application/json" };
  if (token()) headers["Authorization"] = "Bearer " + token();

  const res = await fetch(API + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null
  });

  const data = await res.json().catch(()=>({}));
  if (!res.ok) throw new Error(data.detail || "API Error");
  return data;
}

function setActiveNav() {
  const page = location.pathname.split("/").pop();
  document.querySelectorAll(".nav a").forEach(a=>{
    if (a.getAttribute("href") === page) a.classList.add("active");
  });
}

/* =========================
   LOGIN
========================= */

async function handleLogin(e) {
  e.preventDefault();
  const u = document.getElementById("username").value;
  const p = document.getElementById("password").value;
  const msg = document.getElementById("msg");

  msg.textContent = "Logging in...";
  msg.style.color = "rgba(231,234,243,0.7)";

  try {
    const res = await api("/auth/login", "POST", { username: u, password: p });
    setToken(res.token);
    window.location.href = "dashboard.html";
  } catch (err) {
    msg.textContent = "❌ " + err.message;
    msg.style.color = "#ef4444";
  }
}

/* =========================
   REGISTER (NEW ✅)
========================= */

async function handleRegister(e) {
  e.preventDefault();

  const username = document.getElementById("reg_username").value;
  const password = document.getElementById("reg_password").value;
  const role = document.getElementById("reg_role").value;
  const msg = document.getElementById("reg_msg");

  msg.textContent = "Creating account...";
  msg.style.color = "rgba(231,234,243,0.7)";

  try {
    await api("/auth/register", "POST", { username, password, role });

    msg.textContent = "✅ Account created successfully! Redirecting to login...";
    msg.style.color = "#22c55e";

    setTimeout(() => {
      window.location.href = "index.html";
    }, 1500);

  } catch (err) {
    msg.textContent = "❌ " + err.message;
    msg.style.color = "#ef4444";
  }
}

/* =========================
   DASHBOARD
========================= */

async function dashboardLoad() {
  setActiveNav();

  if (!token()) {
    window.location.href = "index.html";
    return;
  }

  const targets = await api("/targets");
  const scans = await api("/scans");

  document.getElementById("totalTargets").textContent = targets.length;
  document.getElementById("totalScans").textContent = scans.length;
}

/* =========================
   TARGETS (LIST + ADD + EDIT + DELETE)
========================= */

async function loadTargets() {
  setActiveNav();

  if (!token()) {
    window.location.href = "index.html";
    return;
  }

  const t = await api("/targets");
  const tbody = document.getElementById("targetsBody");
  tbody.innerHTML = "";

  t.forEach(x=>{
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${x.id}</td>
      <td><strong>${x.name}</strong></td>
      <td>${x.base_url}</td>
      <td style="display:flex;gap:8px;flex-wrap:wrap;">
        <button class="btn" onclick="editTarget(${x.id}, '${escapeQuotes(x.name)}', '${escapeQuotes(x.base_url)}')">Edit</button>
        <button class="btn" onclick="deleteTarget(${x.id})">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function escapeQuotes(str) {
  return String(str).replace(/'/g, "\\'");
}

async function addTarget(e) {
  e.preventDefault();

  const name = document.getElementById("tname").value;
  const base_url = document.getElementById("turl").value;
  const msg = document.getElementById("tmsg");

  msg.textContent = "Adding target...";
  msg.style.color = "rgba(231,234,243,0.7)";

  try {
    await api("/targets", "POST", { name, base_url });

    msg.textContent = "✅ Target Added";
    msg.style.color = "#22c55e";

    document.getElementById("tname").value = "";
    document.getElementById("turl").value = "";
    loadTargets();

  } catch(err) {
    msg.textContent = "❌ " + err.message;
    msg.style.color = "#ef4444";
  }
}

async function deleteTarget(id) {
  if (!confirm("Are you sure you want to delete this target and all its scans?")) return;

  try {
    await api(`/targets/${id}`, "DELETE");
    alert("✅ Target deleted successfully");
    loadTargets();
  } catch (err) {
    alert("❌ " + err.message);
  }
}

async function editTarget(id, oldName, oldUrl) {
  const newName = prompt("Edit Target Name:", oldName);
  if (newName === null) return;

  const newUrl = prompt("Edit Target URL:", oldUrl);
  if (newUrl === null) return;

  try {
    await api(`/targets/${id}`, "PUT", {
      name: newName,
      base_url: newUrl
    });

    alert("✅ Target updated successfully");
    loadTargets();
  } catch (err) {
    alert("❌ " + err.message);
  }
}

/* =========================
   SCANS
========================= */

async function scansLoad() {
  setActiveNav();

  if (!token()) {
    window.location.href = "index.html";
    return;
  }

  const targets = await api("/targets");
  const scans = await api("/scans");

  const sel = document.getElementById("targetSelect");
  sel.innerHTML = `<option value="">-- Select Target --</option>`;

  targets.forEach(t=>{
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = `${t.name} (${t.base_url})`;
    sel.appendChild(opt);
  });

  const tbody = document.getElementById("scanBody");
  tbody.innerHTML = "";

  scans.forEach(s=>{
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.scan_id}</td>
      <td>${s.target}</td>
      <td>${s.created_at}</td>
      <td><span class="chip low">${s.status}</span></td>
      <td><button class="btn" onclick="openReport(${s.scan_id})">View</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function openReport(id){
  window.location.href = `report.html?scan_id=${id}`;
}

async function runScan(){
  const id = document.getElementById("targetSelect").value;
  const msg = document.getElementById("smsg");

  if (!id){
    msg.textContent = "❌ Please select target";
    msg.style.color = "#ef4444";
    return;
  }

  msg.textContent = "Running scan... please wait";
  msg.style.color = "rgba(231,234,243,0.7)";

  try{
    const res = await api(`/scans/${id}`, "POST");
    msg.textContent = "✅ Scan Completed";
    msg.style.color = "#22c55e";
    openReport(res.scan_id);
  }catch(err){
    msg.textContent = "❌ " + err.message;
    msg.style.color = "#ef4444";
  }
}

/* =========================
   REPORT
========================= */

async function reportLoad(){
  setActiveNav();

  if (!token()) {
    window.location.href = "index.html";
    return;
  }

  const params = new URLSearchParams(window.location.search);
  const scanId = params.get("scan_id");
  document.getElementById("scanId").textContent = "#" + scanId;

  const data = await api(`/scans/${scanId}`);
  document.getElementById("targetUrl").textContent = data.target;

  const clientBox = document.getElementById("clientBox");
  clientBox.innerHTML = "";

  (data.client_report || []).forEach(r=>{
    const sev = r.severity.toLowerCase() === "high"
      ? "high"
      : (r.severity.toLowerCase() === "medium" ? "medium" : "low");

    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <h3>${r.title}</h3>
      <div class="small"><span class="chip ${sev}">${r.severity}</span></div>
      <p class="small" style="margin-top:10px;color:rgba(231,234,243,0.85)">${r.explain}</p>
      <p class="small"><b>Fix:</b> ${r.fix}</p>
    `;
    clientBox.appendChild(div);
  });

  document.getElementById("techJson").textContent = JSON.stringify(data, null, 2);
}

/* =========================
   AI
========================= */

async function askAI(){
  const title = document.getElementById("aititle").value;
  const evidence = document.getElementById("aievidence").value;
  const out = document.getElementById("aiout");

  out.textContent = "Generating AI explanation...";
  try{
    const res = await api(`/ai?title=${encodeURIComponent(title)}&evidence=${encodeURIComponent(evidence)}`);
    out.textContent = res.ai;
  }catch(err){
    out.textContent = "❌ " + err.message;
  }
}
