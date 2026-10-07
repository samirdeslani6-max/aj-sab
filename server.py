import sys
import os
import asyncio
import json
import urllib.request
import time
from aiohttp import web, WSMsgType

sys.stdout.reconfigure(encoding='utf-8')

# ================================================================
# CONFIGURATION & IP WHITELIST
# ================================================================
ALLOWED_IPS = {"127.0.0.1", "localhost", "::1", "::ffff:127.0.0.1"}

WEBHOOK_PETIT   = "https://canary.discord.com/api/webhooks/1557099492962992209/vjabRa_dX0ccNkB8jqfK2DgrwA5cK-4uhA-hRY2K6v6UDWM_RJMyXNgbE7eBpT6hw1es"
WEBHOOK_BONNE   = "https://canary.discord.com/api/webhooks/1557100473113378917/sOWMYYWgNnZiZl8HZHh-Qf9oiP4z6CesP3F3gu2VdcBX8ewg1RSbL1oK-l4tPJnZGZ6r"
WEBHOOK_SUPER   = "https://canary.discord.com/api/webhooks/1557101308706689124/AQSdeYx3my19vSyv3P9cWpDYWKdSV9QJRQwVIsyPSKwM-54MeGQC-owKMt4l74e6WaOA"
WEBHOOK_OG      = "https://canary.discord.com/api/webhooks/1557102248834764845/yJGTE2VBqmr8Jms6rUeTuoS5Cq2TWGhDHB2k0SDlYHH74XweXJz4"
WEBHOOK_PAYMENT = "https://canary.discord.com/api/webhooks/1557125516484411433/kqFZG-ZDxRvsb-G5dBKbEU4GnBcKw1hl-gUHXEfXfGWN26Gl1UNucdm3BoPzGF0JyZ0V"
DISCORD_CLIENT_ID = "1557143518202302577"

CLIENTS = set()
STATS = {"total_steals": 0, "og_steals": 0, "super_steals": 0, "revenue_usd": 0}

LTC_DEPOSIT_ADDRESS = "LcE7XVR5xQaU8EsWfpQpyDexciHutggGaN"
WALLETS_FILE = "user_wallets.json"
PROCESSED_TX_FILE = "processed_txids.json"
KEYS_FILE = "user_keys.json"

def load_wallets():
    if os.path.exists(WALLETS_FILE):
        try:
            with open(WALLETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_wallets(data):
    try:
        with open(WALLETS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[!] Save wallets error: {e}")

def load_processed_txids():
    if os.path.exists(PROCESSED_TX_FILE):
        try:
            with open(PROCESSED_TX_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_txids(txids_set):
    try:
        with open(PROCESSED_TX_FILE, "w", encoding="utf-8") as f:
            json.dump(list(txids_set), f, indent=2)
    except Exception as e:
        print(f"[!] Save processed txids error: {e}")

def load_user_keys():
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_keys(data):
    try:
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[!] Save user keys error: {e}")

def obfuscate_lua_code(source_code, user_key):
    import random
    import string
    
    source_with_key = f'local USER_KEY = "{user_key}"\n' + source_code
    raw_bytes = source_with_key.encode('utf-8')
    xor_key = random.randint(32, 220)
    encrypted_bytes = [b ^ xor_key for b in raw_bytes]
    byte_str = ",".join(map(str, encrypted_bytes))

    var_payload = "_" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    var_key = "_" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    var_decrypt = "_" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    obfuscated_wrapper = f"""--[[
  ===============================================================
  ⚡ PROTECTED BY NIGGA NOTIFIER v2 (LUARMOR ADVANCED PROTECTION)
  Copyright (2026) Nigga Notifier Inc. All Rights Reserved.
  Unauthorized decompilation or dumping will trigger instant kick.
  ===============================================================
--]]
return (function(...)
    local {var_payload} = {{{byte_str}}}
    local {var_key} = {xor_key}
    local bxor = (bit32 and bit32.bxor) or (bit and bit.bxor) or function(a, b) return a end
    local {var_decrypt} = {{}}
    for i = 1, #{var_payload} do
        {var_decrypt}[i] = string.char(bxor({var_payload}[i], {var_key}))
    end
    local code = table.concat({var_decrypt})
    local load_fn = loadstring or load
    local compiled, err = load_fn(code, "NiggaNotifierEngine")
    if not compiled then
        error("[NiggaNotifier] Protection error: " .. tostring(err))
    end
    return compiled(...)
end)(...)"""
    return obfuscated_wrapper

def check_ltc_blockchain_tx(txid):
    if not txid or len(str(txid).strip()) < 20:
        return False, 0.0

    processed = load_processed_txids()
    clean_txid = str(txid).strip().lower()
    if clean_txid in processed:
        return False, 0.0

    url = f"https://api.blockcypher.com/v1/ltc/main/txs/{clean_txid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            outputs = data.get("outputs", [])
            for out in outputs:
                addresses = out.get("addresses", [])
                if LTC_DEPOSIT_ADDRESS in addresses:
                    satoshis = out.get("value", 0)
                    ltc_val = satoshis / 100000000.0
                    processed.add(clean_txid)
                    save_processed_txids(processed)
                    return True, ltc_val
    except Exception as e:
        print(f"[!] LTC API Verification warning: {e}")

    return False, 0.0

# Tier Filtering System
EXCLUDED_FARMER_KEYWORDS = {"dragon", "secret", "celestial", "hydra", "headless", "phoenix", "kraken", "cerberus", "eviledon", "signor carapace", "og", "rainbow", "dark matter"}

def check_tier_filter(plan_name, animal_name, value_num=0):
    name_lower = str(animal_name).lower()
    val = float(value_num or 0)

    if plan_name == "FARMER":
        if val > 1500000000:
            return False
        for kw in EXCLUDED_FARMER_KEYWORDS:
            if kw in name_lower:
                return False
        return True
    elif plan_name == "LOWLIGHT":
        if val > 1500000000:
            return False
        return True
    elif plan_name == "PRO" or plan_name == "ULTRALIGHT":
        return True
    return True

# ================================================================
# HTML REACT + TAILWIND DASHBOARD (FULL ENGLISH & KEY TIMER)
# ================================================================
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIGGA NOTIFIER v2 · Live Ops Hub</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- React & ReactDOM CDN -->
    <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
    <!-- Babel Standalone -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <!-- Google Fonts: Inter & JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'JetBrains+Mono', monospace; }
        .bg-grid-pattern {
            background-size: 36px 36px;
            background-image: 
                linear-gradient(to right, rgba(255, 255, 255, 0.025) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
        }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #08090e; }
        ::-webkit-scrollbar-thumb { background: #1f2430; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #2563eb; }
    </style>
</head>
<body class="bg-[#08090e] bg-grid-pattern text-gray-100 min-h-screen selection:bg-blue-600 selection:text-white antialiased">

    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect } = React;

        const App = () => {
            const [activeTab, setActiveTab] = useState('HOME');
            const [discordUser, setDiscordUser] = useState(null);
            const [walletBalance, setWalletBalance] = useState(0.00);
            const [activePlan, setActivePlan] = useState("FREE");
            const [stealFeed, setStealFeed] = useState([]);
            const [stats, setStats] = useState({ clients: 0, total_steals: 0, og_steals: 0, super_steals: 0 });
            const [showPaymentModal, setShowPaymentModal] = useState(false);
            const [showKeyModal, setShowKeyModal] = useState(false);
            const [purchasedKeyData, setPurchasedKeyData] = useState(null);
            const [isBuyingKey, setIsBuyingKey] = useState(false);
            const [selectedCrypto, setSelectedCrypto] = useState("LTC");
            const [selectedHours, setSelectedHours] = useState(1);
            const [keyTimer, setKeyTimer] = useState(3600);
            const [activeKey, setActiveKey] = useState("NIGGA-FREE-KEY-2026");

            // User Profile fields
            const [usernameInput, setUsernameInput] = useState("look");
            const [avatarUrlInput, setAvatarUrlInput] = useState("https://cdn.discordapp.com/embed/avatars/0.png");
            const [discordIdInput, setDiscordIdInput] = useState("285828205162528768");

            // Deposit Modal fields
            const [depositAmountInput, setDepositAmountInput] = useState(8.00);
            const [depositTxInput, setDepositTxInput] = useState("");
            const [depositStatusMsg, setDepositStatusMsg] = useState({ text: "", type: "info" });
            const [isSubmittingDeposit, setIsSubmittingDeposit] = useState(false);

            // Fetch Real User Balance
            const fetchBalance = async () => {
                const id = discordUser ? discordUser.id : discordIdInput;
                const name = discordUser ? discordUser.username : usernameInput;
                try {
                    const res = await fetch(`/api/get_balance?user_id=${encodeURIComponent(id)}&username=${encodeURIComponent(name)}`);
                    const data = await res.json();
                    if (data.balance !== undefined) {
                        setWalletBalance(data.balance);
                    }
                } catch(e){}
            };

            useEffect(() => {
                fetchBalance();
            }, [discordUser, usernameInput, discordIdInput]);

            // Key countdown timer effect
            useEffect(() => {
                const interval = setInterval(() => {
                    setKeyTimer(prev => (prev > 0 ? prev - 1 : 0));
                }, 1000);
                return () => clearInterval(interval);
            }, []);

            useEffect(() => {
                const hash = window.location.hash;
                if (hash && hash.includes("access_token")) {
                    const params = new URLSearchParams(hash.replace("#", "?"));
                    const token = params.get("access_token");
                    if (token) {
                        fetch("https://discord.com/api/users/@me", {
                            headers: { authorization: `Bearer ${token}` }
                        })
                        .then(res => res.json())
                        .then(user => {
                            if (user && user.username) {
                                const avatarUrl = user.avatar 
                                    ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png` 
                                    : "https://cdn.discordapp.com/embed/avatars/0.png";
                                setDiscordUser({ username: user.username, id: user.id, avatar: avatarUrl });
                                setUsernameInput(user.username);
                                setAvatarUrlInput(avatarUrl);
                                setDiscordIdInput(user.id);
                                window.history.replaceState({}, document.title, window.location.pathname);
                            }
                        })
                        .catch(() => {});
                    }
                }

                let ws = null;
                try {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const host = window.location.host;
                    ws = new WebSocket(`${protocol}//${host}/ws`);
                    ws.onopen = () => console.log("WebSocket connected to Master Hub");
                    ws.onmessage = (evt) => {
                        try {
                            const data = JSON.parse(evt.data);
                            if (data.t === 'dashboard_update') {
                                setStats(prev => ({
                                    ...prev,
                                    clients: data.clients || 0,
                                    total_steals: data.stats ? data.stats.total_steals : 0,
                                    og_steals: data.stats ? data.stats.og_steals : 0,
                                    super_steals: data.stats ? data.stats.super_steals : 0
                                }));
                                if (data.steal_data) {
                                    addSteal(data.steal_data);
                                }
                                fetchBalance();
                            }
                        } catch(e){}
                    };
                    ws.onerror = (err) => console.log("WS Error:", err);
                } catch(e) {
                    console.error("WS connection error:", e);
                }
                return () => { if (ws) ws.close(); };
            }, []);

            const addSteal = (steal) => {
                setStealFeed(prev => [steal, ...prev.slice(0, 50)]);
            };

            const handleDiscordOAuth = () => {
                const redirectUri = encodeURIComponent(window.location.origin + "/");
                const discordAuthUrl = `https://discord.com/api/oauth2/authorize?client_id=1557143518202302577&redirect_uri=${redirectUri}&response_type=token&scope=identify`;
                window.location.href = discordAuthUrl;
            };

            const formatTime = (seconds) => {
                if (seconds <= 0) return "EXPIRED";
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = seconds % 60;
                return `${h.toString().padStart(2, '0')}h ${m.toString().padStart(2, '0')}m ${s.toString().padStart(2, '0')}s`;
            };

            const submitDepositRequest = async () => {
                if (selectedCrypto === 'LTC' && !depositTxInput) {
                    setDepositStatusMsg({ text: "❌ Please enter your Litecoin Transaction Hash (TxID)!", type: "error" });
                    return;
                }
                setIsSubmittingDeposit(true);
                setDepositStatusMsg({ text: "🔍 Verifying transaction...", type: "info" });

                try {
                    const res = await fetch('/api/submit_deposit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            discord_user: discordUser ? discordUser.username : usernameInput,
                            discord_id: discordUser ? discordUser.id : discordIdInput,
                            method: selectedCrypto,
                            amount: depositAmountInput,
                            txid: depositTxInput
                        })
                    });
                    const data = await res.json();
                    if (data.status === 'approved') {
                        setWalletBalance(data.new_balance);
                        setDepositStatusMsg({ text: data.message, type: "success" });
                    } else {
                        setDepositStatusMsg({ text: data.message, type: "info" });
                    }
                } catch(e) {
                    setDepositStatusMsg({ text: "❌ Error connecting to server. Please try again.", type: "error" });
                } finally {
                    setIsSubmittingDeposit(false);
                }
            };

            const rentSubscriptionKey = async (planName, pricePerHour) => {
                const totalPrice = pricePerHour * selectedHours;
                if (walletBalance < totalPrice) {
                    setShowPaymentModal(true);
                    setDepositStatusMsg({ 
                        text: `⚠️ Insufficient Balance! You need $${totalPrice.toFixed(2)} USD to rent ${planName} (${selectedHours}h). Please deposit funds below.`, 
                        type: "error" 
                    });
                    return;
                }

                setIsBuyingKey(true);
                try {
                    const id = discordUser ? discordUser.id : discordIdInput;
                    const name = discordUser ? discordUser.username : usernameInput;

                    const res = await fetch('/api/buy_key', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: id,
                            username: name,
                            plan: planName,
                            hours: selectedHours
                        })
                    });

                    const data = await res.json();
                    if (data.status === 'success') {
                        setWalletBalance(data.new_balance);
                        setActivePlan(`${data.plan} (${data.hours}h)`);
                        setKeyTimer(data.hours * 3600);
                        setActiveKey(data.key);
                        setPurchasedKeyData({
                            key: data.key,
                            loadstring: data.loadstring,
                            plan: data.plan,
                            hours: data.hours
                        });
                        setShowKeyModal(true);
                    } else {
                        alert(`❌ Key Purchase Error: ${data.message || data.error || 'Insufficient balance or server issue.'}`);
                    }
                } catch(e) {
                    alert("❌ Connection error while processing key purchase.");
                } finally {
                    setIsBuyingKey(false);
                }
            };

            return (
                <div className="min-h-screen flex flex-col">

                    {/* TOP NAVBAR (W NOTIFIER STYLE) */}
                    <header className="bg-[#0b0c13]/90 border-b border-gray-800/80 sticky top-0 z-40 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
                        
                        {/* Left Brand Logo */}
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]">
                                <span className="font-black text-lg">⚡</span>
                            </div>
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2">
                                    <span className="font-extrabold tracking-wider text-base text-white">NIGGA NOTIFIER</span>
                                </div>
                                <span className="text-[10px] font-mono font-bold tracking-widest text-blue-400">LIVE OPS</span>
                            </div>
                        </div>

                        {/* Center Menu Navigation */}
                        <nav className="hidden md:flex items-center gap-8">
                            {['HOME', 'SLOTS', 'MARKET', 'LEADERBOARD', 'LIVE FEED'].map(tab => (
                                <button 
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`text-xs font-bold tracking-widest transition uppercase ${activeTab === tab ? 'text-white border-b-2 border-blue-500 pb-1' : 'text-gray-400 hover:text-gray-200'}`}
                                >
                                    {tab}
                                </button>
                            ))}
                        </nav>

                        {/* Right User Bar */}
                        <div className="flex items-center gap-3">
                            {/* Balance Pill */}
                            <div className="px-3.5 py-1.5 bg-[#12141e] border border-gray-800 rounded-full flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                                <span className="text-xs font-mono font-extrabold text-emerald-400">${walletBalance.toFixed(2)}</span>
                            </div>

                            {/* User Profile / Discord Auth */}
                            {discordUser ? (
                                <div className="flex items-center gap-2.5 bg-[#12141e] border border-gray-800 px-3 py-1.5 rounded-xl">
                                    <img src={discordUser.avatar} className="w-6 h-6 rounded-full border border-blue-500" />
                                    <span className="text-xs font-bold text-gray-200">{discordUser.username}</span>
                                    <span className="text-[10px] text-gray-400">⌵</span>
                                </div>
                            ) : (
                                <button 
                                    onClick={handleDiscordOAuth}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg transition flex items-center gap-2"
                                >
                                    <span>👾</span> {usernameInput} <span>⌵</span>
                                </button>
                            )}
                        </div>
                    </header>

                    {/* MAIN CONTENT AREA */}
                    <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-6">

                        {/* TOP ACCOUNT HERO CARD */}
                        <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-6 shadow-2xl relative overflow-hidden flex flex-col md:flex-row justify-between items-center gap-6">
                            
                            {/* Left Account Details */}
                            <div className="flex items-center gap-5 w-full md:w-auto">
                                <img 
                                    src={discordUser ? discordUser.avatar : avatarUrlInput} 
                                    className="w-16 h-16 rounded-2xl border-2 border-gray-700/80 object-cover shadow-lg"
                                />
                                <div className="space-y-1">
                                    <span className="text-[10px] font-bold text-gray-400 tracking-widest uppercase block">ACCOUNT</span>
                                    <h2 className="text-2xl font-black text-white">{discordUser ? discordUser.username : usernameInput}</h2>
                                    <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
                                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                                        <span>Discord linked</span>
                                    </div>
                                </div>
                            </div>

                            {/* Right Balance & Quick Actions */}
                            <div className="flex flex-col md:items-end w-full md:w-auto border-t md:border-t-0 border-gray-800 pt-4 md:pt-0">
                                <span className="text-[10px] font-bold text-gray-400 tracking-widest uppercase block mb-1">BALANCE</span>
                                <div className="text-4xl font-black font-mono text-emerald-400 mb-3">
                                    ${walletBalance.toFixed(2)}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button 
                                        onClick={() => setShowPaymentModal(true)}
                                        className="px-4 py-2 bg-[#171a26] hover:bg-[#202434] border border-gray-700/70 text-gray-200 text-xs font-bold rounded-xl transition"
                                    >
                                        Send
                                    </button>
                                    <button 
                                        onClick={() => setShowPaymentModal(true)}
                                        className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-900/30 transition"
                                    >
                                        Top up
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* STATS ROW (3 GRID CARDS) */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            
                            {/* Stat 1: Deposited */}
                            <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-5 flex flex-col justify-between">
                                <div>
                                    <span className="text-2xl font-black font-mono text-emerald-400">${walletBalance.toFixed(2)}</span>
                                    <span className="text-[10px] font-bold text-gray-400 tracking-widest uppercase block mt-1">TOTAL DEPOSITED</span>
                                </div>
                                <p className="text-[11px] text-gray-500 mt-2">Lifetime money added to your account</p>
                            </div>

                            {/* Stat 2: Active Slots / Bots */}
                            <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-5 flex flex-col justify-between">
                                <div>
                                    <span className="text-2xl font-black font-mono text-blue-400">{stats.clients}</span>
                                    <span className="text-[10px] font-bold text-gray-400 tracking-widest uppercase block mt-1">ACTIVE SLOTS / BOTS</span>
                                </div>
                                <p className="text-[11px] text-gray-500 mt-2">Active WebSocket Roblox clients</p>
                            </div>

                            {/* Stat 3: Rentals / Steals */}
                            <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-5 flex flex-col justify-between">
                                <div>
                                    <span className="text-2xl font-black font-mono text-purple-400">{stats.total_steals}</span>
                                    <span className="text-[10px] font-bold text-gray-400 tracking-widest uppercase block mt-1">RENTALS / TOTAL STEALS</span>
                                </div>
                                <p className="text-[11px] text-gray-500 mt-2">Captured brainrot target steals</p>
                            </div>

                        </div>

                        {/* DISCORD BANNER CARD */}
                        <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-5 flex flex-col sm:flex-row justify-between items-center gap-4">
                            <div>
                                <h3 className="text-sm font-bold text-white">Join our Discord</h3>
                                <p className="text-xs text-gray-400 mt-0.5">Get your Renting role while you rent, and open a support ticket any time.</p>
                            </div>
                            <a 
                                href="https://discord.gg/" 
                                target="_blank"
                                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-md transition whitespace-nowrap"
                            >
                                Join
                            </a>
                        </div>

                        {/* ADD FUNDS / SUBSCRIPTION KEYS CARD */}
                        <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-6 space-y-4">
                            <div className="flex justify-between items-center pb-3 border-b border-gray-800/80">
                                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                    <span className="text-blue-500">⊕</span> Add funds & Subscription Keys
                                </h3>
                                <span className="text-xs font-mono font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">
                                    Key Timer: {formatTime(keyTimer)}
                                </span>
                            </div>

                            {/* Plan Cards Grid */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
                                
                                {/* Farmer */}
                                <div className="bg-[#121420] border border-gray-800 hover:border-blue-500/50 p-4 rounded-xl flex flex-col justify-between transition">
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-xs font-extrabold text-emerald-400">🌾 FARMER</span>
                                            <span className="text-[10px] font-bold text-gray-400">$2/hr</span>
                                        </div>
                                        <ul className="text-[11px] text-gray-400 space-y-1 mb-3">
                                            <li>• Max Value: 1.5B</li>
                                            <li>• Exclude OG Secrets</li>
                                        </ul>
                                    </div>
                                    <button 
                                        onClick={() => rentSubscriptionKey("FARMER", 2.00)}
                                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition"
                                    >
                                        Rent Key
                                    </button>
                                </div>

                                {/* Lowlight */}
                                <div className="bg-[#121420] border border-gray-800 hover:border-blue-500/50 p-4 rounded-xl flex flex-col justify-between transition">
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-xs font-extrabold text-blue-400">💡 LOWLIGHT</span>
                                            <span className="text-[10px] font-bold text-gray-400">$4/hr</span>
                                        </div>
                                        <ul className="text-[11px] text-gray-400 space-y-1 mb-3">
                                            <li>• Fast Teleport</li>
                                            <li>• Filtered Low Logs</li>
                                        </ul>
                                    </div>
                                    <button 
                                        onClick={() => rentSubscriptionKey("LOWLIGHT", 4.00)}
                                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition"
                                    >
                                        Rent Key
                                    </button>
                                </div>

                                {/* Pro */}
                                <div className="bg-[#121420] border border-blue-500/40 p-4 rounded-xl flex flex-col justify-between shadow-lg shadow-blue-950/20">
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-xs font-extrabold text-blue-400">⚡ PRO</span>
                                            <span className="text-[10px] font-bold text-gray-400">$8/hr</span>
                                        </div>
                                        <ul className="text-[11px] text-gray-400 space-y-1 mb-3">
                                            <li>• 1 of 1 Rare Steals</li>
                                            <li>• Included OG Secrets</li>
                                        </ul>
                                    </div>
                                    <button 
                                        onClick={() => rentSubscriptionKey("PRO", 8.00)}
                                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition"
                                    >
                                        Rent Key
                                    </button>
                                </div>

                                {/* Ultralight */}
                                <div className="bg-[#121420] border border-gray-800 hover:border-purple-500/50 p-4 rounded-xl flex flex-col justify-between transition">
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-xs font-extrabold text-purple-400">🚀 ULTRALIGHT</span>
                                            <span className="text-[10px] font-bold text-gray-400">$12/hr</span>
                                        </div>
                                        <ul className="text-[11px] text-gray-400 space-y-1 mb-3">
                                            <li>• Unlimited Brainrots</li>
                                            <li>• Priority Whitelist</li>
                                        </ul>
                                    </div>
                                    <button 
                                        onClick={() => rentSubscriptionKey("ULTRALIGHT", 12.00)}
                                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition"
                                    >
                                        Rent Key
                                    </button>
                                </div>

                            </div>
                        </div>

                        {/* LIVE STEALS FEED CARD */}
                        <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-6 space-y-4">
                            <div className="flex justify-between items-center pb-3 border-b border-gray-800/80">
                                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                    <span>📡</span> Live Steals Stream (Roblox Clients)
                                </h3>
                                <span className="text-xs text-blue-400 font-mono">{stealFeed.length} Captured Steals</span>
                            </div>

                            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                                {stealFeed.length === 0 ? (
                                    <div className="p-8 text-center border border-dashed border-gray-800/80 rounded-xl bg-[#0b0c12]">
                                        <p className="text-xs text-gray-500 font-bold">Waiting for live steals from clients...</p>
                                        <p className="text-[10px] text-gray-600 mt-1">Real-time steals will populate automatically via WebSocket connection.</p>
                                    </div>
                                ) : (
                                    stealFeed.map(s => (
                                        <div key={s.id || Math.random()} className="bg-[#121420] border border-gray-800 p-3 rounded-xl flex items-center justify-between text-xs">
                                            <div>
                                                <span className="font-extrabold text-white mr-2">[{s.tier}] {s.animal}</span>
                                                <span className="text-[10px] text-gray-500 font-mono">Mutation: {s.mutation || 'None'}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-[10px] text-gray-400">Owner: <b className="text-blue-300">{s.stealer}</b></span>
                                                <button 
                                                    onClick={() => navigator.clipboard.writeText(s.jobId)}
                                                    className="px-2.5 py-1 bg-blue-900/40 hover:bg-blue-800 border border-blue-500/30 text-blue-200 text-[10px] rounded font-mono transition"
                                                >
                                                    Copy JobId 📋
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* PROFILE SETTINGS CARD */}
                        <div className="bg-[#0e1018] border border-gray-800/80 rounded-2xl p-6 space-y-4">
                            <span className="text-[10px] font-bold text-gray-400 tracking-widest uppercase block">PROFILE</span>
                            
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs font-bold text-gray-300 block mb-1.5">Username</label>
                                    <input 
                                        type="text" 
                                        value={usernameInput}
                                        onChange={(e) => setUsernameInput(e.target.value)}
                                        className="w-full bg-[#121420] border border-gray-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-gray-300 block mb-1.5">Avatar URL</label>
                                    <input 
                                        type="text" 
                                        value={avatarUrlInput}
                                        onChange={(e) => setAvatarUrlInput(e.target.value)}
                                        className="w-full bg-[#121420] border border-gray-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                                    />
                                </div>
                                <div className="sm:col-span-2">
                                    <label className="text-xs font-bold text-gray-300 block mb-1.5">Discord ID</label>
                                    <input 
                                        type="text" 
                                        value={discordIdInput}
                                        onChange={(e) => setDiscordIdInput(e.target.value)}
                                        className="w-full bg-[#121420] border border-gray-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-blue-500"
                                    />
                                </div>
                            </div>
                        </div>

                    </main>

                    {/* CRYPTO PAYMENT MODAL */}
                    {showPaymentModal && (
                        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                            <div className="bg-[#0e1018] border border-gray-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
                                <button onClick={() => setShowPaymentModal(false)} className="absolute top-4 right-4 text-gray-400 hover:text-white font-bold">✕</button>
                                <h3 className="text-sm font-bold text-white mb-3">💳 Top Up Balance & Select Key Duration</h3>
                                
                                <div className="mb-4">
                                    <label className="text-xs font-bold text-gray-300 block mb-1">Deposit Amount ($USD):</label>
                                    <input 
                                        type="number" 
                                        value={depositAmountInput} 
                                        onChange={(e) => setDepositAmountInput(Number(e.target.value))}
                                        className="w-full bg-[#121420] border border-gray-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                                    />
                                </div>

                                <p className="text-xs text-gray-400 mb-2">Select Payment Method:</p>
                                <div className="grid grid-cols-2 gap-2 mb-4">
                                    {["LTC (Litecoin)", "PayPal"].map(m => {
                                        const isLtc = m.startsWith("LTC");
                                        const isSelected = isLtc ? selectedCrypto === 'LTC' : selectedCrypto === 'PAYPAL';
                                        return (
                                            <button 
                                                key={m}
                                                onClick={() => setSelectedCrypto(isLtc ? 'LTC' : 'PAYPAL')}
                                                className={`py-2 text-xs font-bold rounded-xl border transition ${isSelected ? 'bg-blue-600 border-blue-400 text-white' : 'bg-[#121420] border-gray-800 text-gray-400 hover:text-gray-200'}`}
                                            >
                                                {m}
                                            </button>
                                        );
                                    })}
                                </div>

                                {selectedCrypto === 'LTC' ? (
                                    <div className="space-y-3 mb-4">
                                        <div className="bg-[#121420] p-3 rounded-xl border border-gray-800 text-center">
                                            <p className="text-[10px] text-gray-400 mb-1">Send LTC to Litecoin Address:</p>
                                            <p className="text-xs font-mono font-bold text-emerald-400 break-all select-all p-2 bg-[#0a0b10] rounded-lg border border-emerald-500/30">
                                                LcE7XVR5xQaU8EsWfpQpyDexciHutggGaN
                                            </p>
                                        </div>
                                        <div>
                                            <label className="text-xs font-bold text-gray-300 block mb-1">Enter LTC Transaction Hash (TxID):</label>
                                            <input 
                                                type="text"
                                                placeholder="e.g. 5a1b2c3d4e..."
                                                value={depositTxInput}
                                                onChange={(e) => setDepositTxInput(e.target.value)}
                                                className="w-full bg-[#121420] border border-gray-800 rounded-xl p-2.5 text-xs text-white font-mono focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-3 mb-4">
                                        <div className="bg-[#121420] p-3 rounded-xl border border-gray-800 text-center">
                                            <p className="text-[10px] text-gray-400 mb-1">PayPal Payment:</p>
                                            <p className="text-xs font-bold text-blue-300 p-2 bg-[#0a0b10] rounded-lg border border-blue-500/30">
                                                Open a Discord Support Ticket to receive PayPal details.
                                            </p>
                                        </div>
                                        <div>
                                            <label className="text-xs font-bold text-gray-300 block mb-1">PayPal TxID or Proof Note:</label>
                                            <input 
                                                type="text"
                                                placeholder="e.g. PayPal Transaction # or Note..."
                                                value={depositTxInput}
                                                onChange={(e) => setDepositTxInput(e.target.value)}
                                                className="w-full bg-[#121420] border border-gray-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                                            />
                                        </div>
                                    </div>
                                )}

                                {depositStatusMsg.text && (
                                    <div className={`p-3 rounded-xl text-xs font-bold mb-4 ${depositStatusMsg.type === 'success' ? 'bg-emerald-950/60 border border-emerald-500/50 text-emerald-300' : (depositStatusMsg.type === 'error' ? 'bg-red-950/60 border border-red-500/50 text-red-300' : 'bg-blue-950/60 border border-blue-500/50 text-blue-300')}`}>
                                        {depositStatusMsg.text}
                                    </div>
                                )}

                                <button 
                                    onClick={submitDepositRequest}
                                    disabled={isSubmittingDeposit}
                                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
                                >
                                    {isSubmittingDeposit ? '🔍 Verifying Transaction...' : 'Verify Transaction & Submit Deposit'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* KEY PURCHASED MODAL WITH PROTECTED LOADSTRING */}
                    {showKeyModal && purchasedKeyData && (
                        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
                            <div className="bg-[#0e1018] border border-blue-500/50 rounded-2xl max-w-xl w-full p-6 shadow-[0_0_40px_rgba(37,99,235,0.25)] relative text-left">
                                <button onClick={() => setShowKeyModal(false)} className="absolute top-4 right-4 text-gray-400 hover:text-white font-bold">✕</button>

                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-10 h-10 bg-blue-600/20 border border-blue-500/40 rounded-xl flex items-center justify-center text-blue-400 text-xl font-bold">
                                        🔑
                                    </div>
                                    <div>
                                        <h3 className="text-base font-extrabold text-white">CLÉ GÉNÉRÉE AVEC SUCCÈS !</h3>
                                        <p className="text-xs text-blue-400 font-mono">Plan: {purchasedKeyData.plan} ({purchasedKeyData.hours} Hours Access)</p>
                                    </div>
                                </div>

                                {/* KEY CODE DISPLAY */}
                                <div className="mb-4">
                                    <label className="text-xs font-bold text-gray-300 block mb-1">Votre Clé Privée (Active Key):</label>
                                    <div className="flex items-center gap-2">
                                        <input 
                                            type="text" 
                                            readOnly 
                                            value={purchasedKeyData.key} 
                                            className="w-full bg-[#121420] border border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-emerald-400 font-mono font-bold focus:outline-none"
                                        />
                                        <button 
                                            onClick={() => navigator.clipboard.writeText(purchasedKeyData.key)}
                                            className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-white font-bold text-xs rounded-xl border border-gray-700 transition flex items-center gap-1.5 whitespace-nowrap"
                                        >
                                            📋 Copier Clé
                                        </button>
                                    </div>
                                </div>

                                {/* SECURE LOADSTRING DISPLAY */}
                                <div className="mb-5">
                                    <div className="flex justify-between items-center mb-1">
                                        <label className="text-xs font-bold text-gray-300">Loadstring Protégé (Serveur Obfuscation):</label>
                                        <span className="text-[10px] text-emerald-400 font-mono font-bold">🔒 Anti-Crack Active</span>
                                    </div>
                                    <div className="bg-[#08090f] border border-blue-900/50 rounded-xl p-3.5 relative font-mono text-[11px] text-blue-200 break-all select-all">
                                        {purchasedKeyData.loadstring}
                                    </div>
                                    <button 
                                        onClick={() => navigator.clipboard.writeText(purchasedKeyData.loadstring)}
                                        className="w-full mt-2.5 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-extrabold text-xs rounded-xl shadow-lg transition flex items-center justify-center gap-2 tracking-wider"
                                    >
                                        ⚡ COPIER LE LOADSTRING DIRECTEMENT
                                    </button>
                                </div>

                                {/* EXECUTOR INSTRUCTIONS */}
                                <div className="bg-[#121420] border border-gray-800/80 rounded-xl p-3 text-[11px] text-gray-400 space-y-1">
                                    <p className="font-bold text-white flex items-center gap-1.5">
                                        <span>💡</span> Comment utiliser :
                                    </p>
                                    <p>1. Copiez le <b>loadstring</b> ci-dessus et collez-le dans votre exécuteur (Solara, Wave, Xeno, Delta, Swift, Fluxus, etc.).</p>
                                    <p>2. La source du script est dynamiquement obfusquée et protégée par le serveur backend. Aucun code source n'est exposé en clair.</p>
                                </div>

                                <button 
                                    onClick={() => setShowKeyModal(false)}
                                    className="w-full mt-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 font-bold text-xs rounded-xl transition"
                                >
                                    Fermer
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            );
        };

        ReactDOM.createRoot(document.getElementById('root')).render(<App />);
    </script>
</body>
</html>"""

# ================================================================
# DISCORD NOTIFICATIONS
# ================================================================
OG_KEYWORDS = {"dragon", "secret", "celestial", "hydra", "headless", "phoenix", "kraken", "cerberus", "eviledon", "la secret combinasion", "los secret combinasionas", "og", "rainbow", "dark matter", "galaxy"}
SUPER_KEYWORDS = {"la supreme combinasion", "la grande combinasion", "mythic", "nuclearo", "capitano", "bombardiro", "chicleteira", "torrtuginni", "arcadragon", "los dragons", "golden", "gold"}
BONNE_KEYWORDS = {"cappuccino", "burrito", "bambini", "avocado", "crocodilo", "chihuanini", "gato", "capibaro", "rare", "epic"}

def classify_target(animal_name, mutation=""):
    name_lower = str(animal_name).lower()
    mut_lower = str(mutation).lower()
    full_str = f"{name_lower} {mut_lower}"

    for kw in OG_KEYWORDS:
        if kw in full_str: return "OG", WEBHOOK_OG, 0xFF0055
    for kw in SUPER_KEYWORDS:
        if kw in full_str: return "SUPER", WEBHOOK_SUPER, 0x9B59B6
    for kw in BONNE_KEYWORDS:
        if kw in full_str: return "BONNE", WEBHOOK_BONNE, 0x3498DB

    return "PETIT", WEBHOOK_PETIT, 0x2ECC71

def send_discord_webhook(webhook_url, animal, mutation, stealer, job_id, place_id, tier, color):
    if not webhook_url: return

    embed = {
        "title": f"⚡ NIGGA NOTIFIER [{tier} LOG]",
        "color": color,
        "fields": [
            {"name": "🐾 Brainrot / Animal", "value": f"**{animal}**", "inline": True},
            {"name": "✦ Mutation", "value": f"`{mutation if mutation else 'None'}`", "inline": True},
            {"name": "👤 Stealer / Owner", "value": f"`{stealer}`", "inline": True},
            {"name": "🌐 JobId", "value": f"```{job_id}```", "inline": False},
            {"name": "⚡ Quick Join", "value": f"PlaceID: `{place_id}`", "inline": True}
        ],
        "footer": {"text": "Nigga Notifier v2 · Auto-Join System"}
    }

    payload = json.dumps({"embeds": [embed]}).encode('utf-8')
    req = urllib.request.Request(
        webhook_url, data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as resp: pass
    except Exception as e:
        print(f"[!] Discord Webhook Error: {e}")

def send_discord_payment_notification(user_tag, plan, duration, price, crypto, tx_hash):
    embed = {
        "title": "💰 CRYPTO PAYMENT RECEIVED!",
        "color": 0x00E676,
        "fields": [
            {"name": "👤 Discord User", "value": f"`{user_tag}`", "inline": True},
            {"name": "💎 Plan & Duration", "value": f"**{plan}** ({duration} Hours Key)", "inline": True},
            {"name": "🪙 Crypto Used", "value": f"`{crypto}` (${price} USD)", "inline": True},
            {"name": "🔗 TxHash", "value": f"```{tx_hash}```", "inline": False}
        ],
        "footer": {"text": "Nigga Finder v2 · Crypto Payment Gateway"}
    }
    payload = json.dumps({"embeds": [embed]}).encode('utf-8')
    req = urllib.request.Request(
        WEBHOOK_PAYMENT, data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"[PAYMENT] Webhook Success for {user_tag} ({plan})")
    except Exception as e:
        print(f"[!] Payment Webhook Error: {e}")

# ================================================================
# AIOHTTP SERVER (COMBINED DASHBOARD HTTP & WEBSOCKET MASTER)
# ================================================================
async def broadcast_dashboard_update(log_text="", tier="PETIT", steal_obj=None):
    payload = json.dumps({
        "t": "dashboard_update",
        "clients": len(CLIENTS),
        "stats": STATS,
        "log": log_text,
        "tier": tier,
        "steal_data": steal_obj
    })
    for client in list(CLIENTS):
        try:
            await client.send_str(payload)
        except Exception:
            pass

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    CLIENTS.add(ws)
    client_ip = request.remote
    print(f"[+] Client Connected ({client_ip}) | Total: {len(CLIENTS)}")
    await broadcast_dashboard_update(f"Client connected (Total: {len(CLIENTS)})")

    try:
        async for message in ws:
            if message.type == WSMsgType.TEXT:
                try:
                    data = json.loads(message.data)
                    msg_type = data.get("t")

                    if msg_type == "ping":
                        await ws.send_str(json.dumps({"t": "pong"}))

                    elif msg_type == "auth_key":
                        key = data.get("key")
                        if key and "NIGGA" in key:
                            await ws.send_str(json.dumps({"t": "auth_success", "status": "valid"}))
                        else:
                            await ws.send_str(json.dumps({"t": "key_expired", "reason": "Invalid key or expired"}))

                    elif msg_type == "notify_target":
                        job_id = data.get("jobId", "Unknown")
                        place_id = data.get("placeId", 0)
                        info = data.get("info", {})

                        animal = info.get("animal", "Unknown Animal")
                        mutation = info.get("mutation", "")
                        stealer = info.get("stealer", "Unknown")

                        tier, webhook_url, color = classify_target(animal, mutation)
                        send_discord_webhook(webhook_url, animal, mutation, stealer, job_id, place_id, tier, color)

                        STATS["total_steals"] += 1
                        if tier == "OG": STATS["og_steals"] += 1
                        if tier == "SUPER": STATS["super_steals"] += 1

                        steal_obj = {
                            "id": str(time.time()),
                            "animal": animal,
                            "mutation": mutation,
                            "stealer": str(stealer),
                            "jobId": job_id,
                            "placeId": place_id,
                            "tier": tier,
                            "time": time.strftime("%H:%M:%S")
                        }

                        broadcast_payload = json.dumps({
                            "t": "join_target",
                            "jobId": job_id,
                            "placeId": place_id,
                            "animal": animal,
                            "mutation": mutation
                        })

                        for client in list(CLIENTS):
                            try:
                                await client.send_str(broadcast_payload)
                            except Exception:
                                pass

                        await broadcast_dashboard_update(f"Steal Detected: {animal} ({tier})", tier=tier, steal_obj=steal_obj)

                except Exception as e:
                    print(f"[!] WebSocket message error: {e}")
            elif message.type == WSMsgType.ERROR:
                print(f"[!] WebSocket error: {ws.exception()}")
    finally:
        CLIENTS.remove(ws)
        print(f"[-] Client Disconnected ({client_ip}) | Total: {len(CLIENTS)}")
        await broadcast_dashboard_update(f"Client disconnected (Total: {len(CLIENTS)})")

    return ws

async def handle_dashboard(request):
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await websocket_handler(request)
    return web.Response(text=DASHBOARD_HTML, content_type="text/html", charset="utf-8")

async def handle_get_balance(request):
    user_id = request.query.get("user_id", "")
    username = request.query.get("username", "")
    wallets = load_wallets()
    bal = wallets.get(str(user_id), wallets.get(str(username), 0.0))
    return web.json_response({"balance": float(bal)})

async def handle_payment_notify(request):
    try:
        data = await request.json()
        user = data.get("discord_user", "Unknown")
        plan = data.get("plan", "PRO")
        duration = data.get("duration_hours", 1)
        price = data.get("price", 8)
        crypto = data.get("crypto", "BTC")
        tx_hash = data.get("tx_hash", "0x0000")

        send_discord_payment_notification(user, plan, duration, price, crypto, tx_hash)
        return web.json_response({"status": "ok"})
    except Exception as e:
        print(f"[!] Error Payment API: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_add_wallet(request):
    try:
        data = await request.json()
        user_id = str(data.get("user_id", ""))
        username = str(data.get("username", "Unknown"))
        amount = float(data.get("amount", 0.0))
        admin = data.get("admin", "Admin")

        wallets = load_wallets()
        key = user_id if user_id and user_id != "Unknown" else username
        current_bal = wallets.get(key, 0.0)
        new_bal = current_bal + amount
        wallets[key] = new_bal
        if username and username != key:
            wallets[username] = new_bal
        save_wallets(wallets)

        print(f"[WALLET API] Added ${amount:.2f} USD to user {username} ({key}) by admin {admin}. New balance: ${new_bal:.2f}")

        # Broadcast live wallet update to all connected dashboard websockets!
        await broadcast_dashboard_update(f"Wallet updated: ${amount:.2f} credited to {username}")

        return web.json_response({"status": "ok", "message": "Wallet balance credited successfully", "new_balance": new_bal})
    except Exception as e:
        print(f"[!] Error Wallet API: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_submit_deposit(request):
    try:
        data = await request.json()
        user_id = str(data.get("discord_id", ""))
        username = str(data.get("discord_user", "Unknown"))
        method = str(data.get("method", "LTC")).upper()
        amount = float(data.get("amount", 8.0))
        txid = str(data.get("txid", "")).strip()

        # 1. Check LTC Blockchain Auto-Verification
        if method == "LTC" and txid:
            verified, ltc_val = check_ltc_blockchain_tx(txid)
            if verified:
                wallets = load_wallets()
                key = user_id if user_id else username
                new_bal = wallets.get(key, 0.0) + amount
                wallets[key] = new_bal
                if username and username != key:
                    wallets[username] = new_bal
                save_wallets(wallets)
                
                send_discord_payment_notification(username, "AUTO_BLOCKCHAIN_LTC", 1, amount, "LTC (Verified)", txid)
                await broadcast_dashboard_update(f"LTC Auto Deposit Verified: ${amount:.2f} credited to {username}")
                return web.json_response({
                    "status": "approved", 
                    "message": f"✅ LTC Transaction Verified on Blockchain! ${amount:.2f} USD added to your wallet.",
                    "new_balance": new_bal
                })

        # 2. Manual / Pending Approval Notification for Admin
        send_discord_payment_notification(username, "DEPOSIT_REQUEST", 1, amount, method, txid if txid else "No TxID provided")
        return web.json_response({
            "status": "pending",
            "message": f"📩 Deposit Request of ${amount:.2f} USD submitted! Admin notified on Discord. Admin will verify your payment and run !5wallet to approve."
        })
    except Exception as e:
        print(f"[!] Error Submit Deposit API: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_buy_key(request):
    try:
        data = await request.json()
        user_id = str(data.get("user_id", data.get("discord_id", ""))).strip()
        username = str(data.get("username", data.get("discord_user", "Unknown"))).strip()
        plan = str(data.get("plan", "PRO")).upper()
        hours = int(data.get("hours", 1))

        prices = {"FARMER": 2.0, "LOWLIGHT": 4.0, "PRO": 8.0, "ULTRALIGHT": 12.0}
        price_per_hour = prices.get(plan, 8.0)
        total_price = price_per_hour * hours

        wallets = load_wallets()
        # Lookup balance by user_id or username
        current_bal = wallets.get(user_id, wallets.get(username, 0.0))

        if current_bal < total_price:
            return web.json_response({
                "status": "error",
                "message": f"Insufficient Wallet Balance! You need ${total_price:.2f} USD to rent {plan} ({hours}h). Current balance: ${current_bal:.2f} USD."
            }, status=400)

        # Deduct balance from all matching keys (user_id and username)
        new_bal = current_bal - total_price
        if user_id:
            wallets[user_id] = new_bal
        if username and username != "Unknown":
            wallets[username] = new_bal
        save_wallets(wallets)

        # Generate unique key
        import uuid
        generated_key = f"NIGGA-{plan}-{uuid.uuid4().hex[:8].upper()}"
        expires_at = time.time() + (hours * 3600)

        keys_db = load_user_keys()
        keys_db[generated_key] = {
            "plan": plan,
            "user_id": user_id,
            "username": username,
            "expires_at": expires_at,
            "created_at": time.time()
        }
        save_user_keys(keys_db)

        # Build loadstring URL
        host = request.host
        protocol = "https" if request.secure or "onrender.com" in host else "http"
        loadstring_code = f'loadstring(game:HttpGet("{protocol}://{host}/api/get_script?key={generated_key}"))()'

        send_discord_payment_notification(username, f"KEY_RENT_{plan}", hours, total_price, "WALLET", generated_key)
        await broadcast_dashboard_update(f"Key Rented: {plan} ({hours}h) by {username}")

        return web.json_response({
            "status": "success",
            "key": generated_key,
            "plan": plan,
            "hours": hours,
            "loadstring": loadstring_code,
            "new_balance": new_bal
        })
    except Exception as e:
        print(f"[!] Buy Key API Error: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_get_script(request):
    user_key = request.query.get("key", "").strip()

    if not user_key:
        error_lua = 'error("[Nigga Notifier] KEY REQUIRED! Rent a subscription key at https://aj-sab.onrender.com")'
        return web.Response(text=error_lua, content_type="text/plain", charset="utf-8")

    keys_db = load_user_keys()
    # Case-insensitive lookup
    key_info = keys_db.get(user_key) or keys_db.get(user_key.upper())
    if not key_info:
        key_info = next((v for k, v in keys_db.items() if k.upper() == user_key.upper()), None)

    # Auto-validate any NIGGA- or KEY- prefix key so Render restarts never break active keys
    if not key_info and (user_key.upper().startswith("NIGGA-") or user_key.upper().startswith("KEY-")):
        key_info = {
            "plan": "PRO",
            "user_id": "auto",
            "username": "auto_renter",
            "expires_at": time.time() + 72 * 3600,
            "created_at": time.time()
        }
        keys_db[user_key.upper()] = key_info
        save_user_keys(keys_db)

    if not key_info:
        is_valid = False
    else:
        expires_at = key_info.get("expires_at", 0)
        is_valid = time.time() <= expires_at

    if not is_valid:
        error_lua = 'error("[Nigga Notifier] INVALID OR EXPIRED KEY! Rent a valid subscription key at https://aj-sab.onrender.com")'
        return web.Response(text=error_lua, content_type="text/plain", charset="utf-8")

    # Read base source code
    script_path = "autojoiner.lua"
    if not os.path.exists(script_path):
        script_path = "autojoiner_protected.lua"

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            raw_code = f.read()

        # Obfuscate dynamically with key embedded!
        protected_lua = obfuscate_lua_code(raw_code, user_key)
        return web.Response(text=protected_lua, content_type="text/plain", charset="utf-8")
    except Exception as e:
        print(f"[!] Error serving protected script: {e}")
        return web.Response(text=f'error("[Nigga Notifier] Script Load Error: {e}")', content_type="text/plain", charset="utf-8")

async def start_discord_bot(app):
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    if bot_token:
        try:
            from discord_bot import bot
            asyncio.create_task(bot.start(bot_token))
            print("[+] Discord Bot launched in background via server.py")
        except Exception as e:
            print(f"[!] Discord Bot startup error in server: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.on_startup.append(start_discord_bot)
    app.router.add_get('/', handle_dashboard)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/api/get_balance', handle_get_balance)
    app.router.add_get('/api/get_script', handle_get_script)
    app.router.add_post('/api/buy_key', handle_buy_key)
    app.router.add_post('/api/submit_deposit', handle_submit_deposit)
    app.router.add_post('/api/payment_notify', handle_payment_notify)
    app.router.add_post('/api/add_wallet', handle_add_wallet)

    print(f"[+] Server online on port {port} (Combined HTTP Dashboard & WebSocket Master)")
    web.run_app(app, host="0.0.0.0", port=port)
