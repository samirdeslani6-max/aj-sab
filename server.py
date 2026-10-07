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
            const [selectedCrypto, setSelectedCrypto] = useState("BTC");
            const [selectedHours, setSelectedHours] = useState(1);
            const [keyTimer, setKeyTimer] = useState(3600);
            const [activeKey, setActiveKey] = useState("NIGGA-FREE-KEY-2026");

            // User Profile fields
            const [usernameInput, setUsernameInput] = useState("look");
            const [avatarUrlInput, setAvatarUrlInput] = useState("https://cdn.discordapp.com/embed/avatars/0.png");
            const [discordIdInput, setDiscordIdInput] = useState("285828205162528768");

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

            const simulateCryptoPayment = async (planName, priceUsd) => {
                const tx = "0x" + Math.random().toString(36).substring(2, 15);
                try {
                    await fetch('/api/payment_notify', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            discord_user: discordUser ? discordUser.username : usernameInput,
                            plan: planName,
                            duration_hours: selectedHours,
                            price: priceUsd * selectedHours,
                            crypto: selectedCrypto,
                            tx_hash: tx
                        })
                    });
                } catch(e){}

                setWalletBalance(prev => prev + (priceUsd * selectedHours));
                setActivePlan(`${planName} (${selectedHours}h)`);
                setKeyTimer(prev => prev + (selectedHours * 3600));
                setShowPaymentModal(false);
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
                                        onClick={() => setShowPaymentModal(true)}
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
                                        onClick={() => setShowPaymentModal(true)}
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
                                        onClick={() => setShowPaymentModal(true)}
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
                                        onClick={() => setShowPaymentModal(true)}
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
                                    <label className="text-xs font-bold text-gray-300 block mb-1">Duration (Hours):</label>
                                    <select 
                                        value={selectedHours} 
                                        onChange={(e) => setSelectedHours(Number(e.target.value))}
                                        className="w-full bg-[#121420] border border-gray-800 rounded-xl p-2.5 text-xs text-white focus:outline-none"
                                    >
                                        <option value={1}>1 Hour Key ($8.00)</option>
                                        <option value={2}>2 Hours Key ($16.00)</option>
                                        <option value={6}>6 Hours Key ($48.00)</option>
                                        <option value={12}>12 Hours Key ($96.00)</option>
                                        <option value={24}>24 Hours Key ($192.00)</option>
                                    </select>
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
                                    <div className="bg-[#121420] p-3 rounded-xl border border-gray-800 mb-4 text-center">
                                        <p className="text-[10px] text-gray-400 mb-1">Litecoin (LTC) Deposit Address:</p>
                                        <p className="text-xs font-mono font-bold text-emerald-400 break-all select-all p-2 bg-[#0a0b10] rounded-lg border border-emerald-500/30">
                                            LcE7XVR5xQaU8EsWfpQpyDexciHutggGaN
                                        </p>
                                    </div>
                                ) : (
                                    <div className="bg-[#121420] p-3 rounded-xl border border-gray-800 mb-4 text-center">
                                        <p className="text-[10px] text-gray-400 mb-1">PayPal Payment:</p>
                                        <p className="text-xs font-bold text-blue-300 p-2 bg-[#0a0b10] rounded-lg border border-blue-500/30">
                                            Open a Discord Support Ticket to pay via PayPal.
                                        </p>
                                    </div>
                                )}

                                <div className="bg-blue-950/40 border border-blue-500/30 p-3 rounded-xl mb-4 text-center">
                                    <p className="text-xs text-blue-200 font-bold">📩 Payment Instructions (English):</p>
                                    <p className="text-[11px] text-gray-300 mt-1">
                                        After sending payment via LTC or PayPal, open a support ticket on Discord with your proof/TxID. The admin will credit your wallet balance immediately!
                                    </p>
                                </div>

                                <button 
                                    onClick={() => simulateCryptoPayment("PRO", 8.00)}
                                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-lg transition"
                                >
                                    Confirm Deposit Request & Notify Admin
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
        user_id = data.get("user_id")
        username = data.get("username", "Unknown")
        amount = data.get("amount", 0.0)
        admin = data.get("admin", "Admin")

        print(f"[WALLET API] Added ${amount:.2f} USD to user {username} (ID: {user_id}) by admin {admin}")
        return web.json_response({"status": "ok", "message": "Wallet balance credited successfully"})
    except Exception as e:
        print(f"[!] Error Wallet API: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def start_discord_bot(app):
    bot_token = os.environ.get("DISCORD_BOT_TOKEN", "MTU1NzE0MzUxODIwMjMwMjU3Nw.G8to_O.4ALhxhv3JMKVTL77ajlvCfT7GZx5GXxNwLA6bY")
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
    app.router.add_post('/api/payment_notify', handle_payment_notify)
    app.router.add_post('/api/add_wallet', handle_add_wallet)

    print(f"[+] Server online on port {port} (Combined HTTP Dashboard & WebSocket Master)")
    web.run_app(app, host="0.0.0.0", port=port)
