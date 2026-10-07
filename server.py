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
    <title>NIGGA FINDER v2 · Master Hub</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- React & ReactDOM CDN -->
    <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
    <!-- Babel Standalone -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <!-- Zdog & GSAP -->
    <script src="https://unpkg.com/zdog@1/dist/zdog.dist.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/2.1.3/TweenMax.min.js"></script>
    <style>
        @keyframes pulseGlow {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.1); }
        }
        .aurora-blob { animation: pulseGlow 6s infinite ease-in-out; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #08080c; }
        ::-webkit-scrollbar-thumb { background: #252538; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #ec4899; }
    </style>
</head>
<body class="bg-[#07070b] text-gray-100 font-sans min-h-screen overflow-x-hidden antialiased selection:bg-pink-500 selection:text-white">

    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;

        // 3D Character Renderer (Zdog + GSAP)
        const Interactive3DCharacter = () => {
            const canvasRef = useRef(null);

            useEffect(() => {
                let animationFrameId;
                if (!canvasRef.current || !window.Zdog || !window.TweenMax) return;

                const Zdog = window.Zdog;
                const TweenMax = window.TweenMax;
                const Sine = window.Sine;

                const PALETTE = {
                    dark: "#080000",
                    light: "#fff",
                    skin: "hsl(320, 80%, 65%)",
                    skinHighlight: "hsl(320, 90%, 75%)",
                    skinShadow: "hsl(320, 60%, 45%)",
                };

                const illo = new Zdog.Illustration({
                    element: canvasRef.current,
                    resize: 'fullscreen',
                    onResize: function(w, h) { this.zoom = Math.min(w, h) / 360; },
                    dragRotate: true,
                });

                const headAnchor = new Zdog.Anchor({ addTo: illo, translate: { y: -40 } });
                new Zdog.Group({ addTo: headAnchor });
                new Zdog.Shape({ addTo: headAnchor.children[0], stroke: 210, color: PALETTE.skinShadow, path: [{ x: -4 }, { x: 4 }] });
                new Zdog.Shape({ addTo: headAnchor.children[0], stroke: 200, color: PALETTE.skin, translate: { x: -4 } });

                const eyeAnchor = new Zdog.Anchor({ addTo: headAnchor, translate: { x: -60, y: -25, z: 80 }, rotate: { y: Zdog.TAU / 11 } });
                const eyeGroup = new Zdog.Group({ addTo: eyeAnchor });
                
                const eye = new Zdog.Shape({
                    addTo: eyeGroup, fill: true, stroke: 3, color: PALETTE.dark, translate: { y: 6 },
                    path: [{ x: 0, y: 0, z: 3 }, { bezier: [{ x: 20, y: 0, z: 3 }, { x: 30, y: 18, z: 0 }, { x: 30, y: 30, z: 0 }] }, { bezier: [{ x: 30, y: 45, z: 0 }, { x: 20, y: 55, z: 3 }, { x: 0, y: 55, z: 3 }] }]
                });
                eye.copy({ addTo: eye, fill: true, color: PALETTE.light, scale: 0.4, translate: { x: -8, y: 8, z: 3 } });
                eyeAnchor.copyGraph({ translate: { x: 60, y: -25, z: 80 }, rotate: { y: Zdog.TAU / -11 } });

                const bodyAnchor = new Zdog.Anchor({ addTo: illo, translate: { y: 75 } });
                const bodyUpper = new Zdog.Shape({ addTo: bodyAnchor, stroke: 58, fill: true, color: PALETTE.skinShadow, translate: { y: 6 } });
                bodyUpper.copy({ stroke: 52, color: PALETTE.skin, translate: { x: -3 } });

                TweenMax.to(bodyUpper.scale, 0.6, { x: 0.94, y: 0.96, repeat: -1, yoyo: true, ease: Sine.easeInOut });

                const handleMouseMove = (e) => {
                    if (!canvasRef.current) return;
                    const rect = canvasRef.current.getBoundingClientRect();
                    const rotX = (e.clientX - (rect.left + rect.width / 2)) / Zdog.TAU;
                    const rotY = -(e.clientY - (rect.top + rect.height / 2)) / Zdog.TAU;
                    TweenMax.to(headAnchor.rotate, 0.4, { x: rotY / 120, y: -rotX / 120, ease: Sine.easeOut });
                    TweenMax.to(bodyAnchor.rotate, 0.4, { x: rotY / 240, y: -rotX / 240, ease: Sine.easeOut });
                };

                document.body.addEventListener("mousemove", handleMouseMove);

                const render = () => {
                    illo.updateRenderGraph();
                    animationFrameId = requestAnimationFrame(render);
                };
                render();

                return () => {
                    cancelAnimationFrame(animationFrameId);
                    document.body.removeEventListener("mousemove", handleMouseMove);
                };
            }, []);

            return <canvas ref={canvasRef} className="w-full h-full block" />;
        };

        const App = () => {
            const [discordUser, setDiscordUser] = useState(null);
            const [walletBalance, setWalletBalance] = useState(0.00);
            const [activePlan, setActivePlan] = useState("FREE");
            const [stealFeed, setStealFeed] = useState([]);
            const [stats, setStats] = useState({ clients: 0, total_steals: 0, og_steals: 0, super_steals: 0 });
            const [showPaymentModal, setShowPaymentModal] = useState(false);
            const [selectedCrypto, setSelectedCrypto] = useState("BTC");
            const [selectedHours, setSelectedHours] = useState(1);
            const [keyTimer, setKeyTimer] = useState(3600); // Default 1 hour in seconds
            const [activeKey, setActiveKey] = useState("NIGGA-FREE-KEY-2026");

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
                                setDiscordUser({ username: `@${user.username}`, avatar: avatarUrl });
                                window.history.replaceState({}, document.title, window.location.pathname);
                            }
                        })
                        .catch(() => {});
                    }
                }

                const ws = new WebSocket('ws://' + location.hostname + ':8081');
                ws.onopen = () => {};
                ws.onmessage = (evt) => {
                    try {
                        const data = JSON.parse(evt.data);
                        if (data.t === 'dashboard_update') {
                            setStats(prev => ({
                                ...prev,
                                clients: data.clients,
                                total_steals: data.stats.total_steals,
                                og_steals: data.stats.og_steals,
                                super_steals: data.stats.super_steals
                            }));
                            if (data.steal_data) {
                                addSteal(data.steal_data);
                            }
                        }
                    } catch(e){}
                };
                return () => ws.close();
            }, []);

            const addSteal = (steal) => {
                setStealFeed(prev => [steal, ...prev.slice(0, 50)]);
            };

            const handleDiscordOAuth = () => {
                const redirectUri = encodeURIComponent(window.location.origin + "/");
                const discordAuthUrl = `https://discord.com/api/oauth2/authorize?client_id=1557143518202302577&redirect_uri=${redirectUri}&response_type=token&scope=identify`;
                window.location.href = discordAuthUrl;
            };

            const extendKeyTime = (hoursToAdd) => {
                setKeyTimer(prev => prev + (hoursToAdd * 3600));
            };

            const formatTime = (seconds) => {
                if (seconds <= 0) return "00h 00m 00s (EXPIRED)";
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
                            discord_user: discordUser ? discordUser.username : "Anonymous User",
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
                <div className="min-h-screen flex flex-col md:flex-row">

                    {/* LEFT SIDEBAR: LIVE STEAL FEED */}
                    <aside className="w-full md:w-96 bg-[#0c0c14] border-r border-pink-500/20 p-5 flex flex-col h-auto md:h-screen sticky top-0 z-20 shadow-2xl">
                        
                        {/* Sidebar Header Logo */}
                        <div className="flex items-center justify-between pb-4 border-b border-pink-900/30 mb-5">
                            <div className="relative inline-flex items-center px-5 py-2.5 bg-[#17122b] border border-pink-500/70 rounded-full shadow-[0_0_15px_rgba(236,72,153,0.3)]">
                                <div className="absolute -top-1 left-3 w-2.5 h-2.5 bg-pink-500 rounded-full shadow-[0_0_8px_#ec4899] animate-pulse"></div>
                                <span className="text-xl mr-3 text-amber-400 filter drop-shadow-[0_0_6px_#f59e0b]">⚡</span>
                                <span className="font-mono text-sm font-bold tracking-[0.25em] text-pink-300">
                                    NIGGA FINDER
                                </span>
                                <div className="absolute -bottom-1.5 left-6 flex space-x-1">
                                    <div className="w-2.5 h-1.5 bg-pink-500 rounded-b-full shadow-[0_0_5px_#ec4899]"></div>
                                    <div className="w-2.5 h-1.5 bg-pink-500 rounded-b-full shadow-[0_0_5px_#ec4899]"></div>
                                    <div className="w-2.5 h-1.5 bg-pink-500 rounded-b-full shadow-[0_0_5px_#ec4899]"></div>
                                </div>
                            </div>
                            <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-extrabold border border-emerald-500/30 flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> LIVE
                            </span>
                        </div>

                        {/* Steals Stream Header */}
                        <div className="flex justify-between items-center mb-3 text-xs font-bold text-gray-400 uppercase tracking-wider">
                            <span>📡 Live Steals Feed</span>
                            <span className="text-pink-400">{stealFeed.length} Steals</span>
                        </div>

                        {/* Steals Scrollable Feed */}
                        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                            {stealFeed.length === 0 ? (
                                <div className="p-6 text-center border border-dashed border-gray-800 rounded-2xl my-4 bg-[#0a0a10]">
                                    <span className="text-2xl mb-2 block">📡</span>
                                    <p className="text-xs text-gray-400 font-bold">Waiting for real steals...</p>
                                    <p className="text-[10px] text-gray-600 mt-1">Live steals captured from Roblox clients will appear here real-time.</p>
                                </div>
                            ) : (
                                stealFeed.map(s => {
                                    let badgeStyle = "border-emerald-500/40 bg-emerald-500/10 text-emerald-300 shadow-[0_0_10px_rgba(16,185,129,0.2)]";
                                    if (s.tier === "OG") badgeStyle = "border-pink-500/60 bg-pink-500/20 text-pink-300 shadow-[0_0_15px_rgba(236,72,153,0.4)] animate-pulse";
                                    if (s.tier === "SUPER") badgeStyle = "border-purple-500/60 bg-purple-500/20 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.4)]";
                                    if (s.tier === "BONNE") badgeStyle = "border-blue-500/40 bg-blue-500/10 text-blue-300";

                                    return (
                                        <div key={s.id || Math.random()} className="bg-[#12121e] border border-gray-800/80 hover:border-pink-500/40 p-3.5 rounded-xl transition duration-200 shadow-md">
                                            <div className="flex justify-between items-start mb-1.5">
                                                <span className={`px-2 py-0.5 rounded-md border text-[10px] font-black ${badgeStyle}`}>
                                                    [{s.tier}] {s.mutation || 'Secret'}
                                                </span>
                                                <span className="text-[10px] font-mono text-gray-500">{s.time}</span>
                                            </div>
                                            <p className="text-xs font-black text-white truncate mb-1">{s.animal}</p>
                                            <div className="flex justify-between items-center text-[10px] text-gray-400">
                                                <span>Stealer: <b className="text-pink-300">{s.stealer}</b></span>
                                                <button 
                                                    onClick={() => navigator.clipboard.writeText(s.jobId)}
                                                    className="px-2 py-0.5 bg-pink-900/40 hover:bg-pink-800 text-pink-200 rounded font-mono text-[9px] transition"
                                                >
                                                    JobId 📋
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                        {discordUser && (
                            <div className="mt-4 pt-3 border-t border-pink-900/30">
                                <button 
                                    onClick={() => setDiscordUser(null)}
                                    className="w-full py-2 bg-red-950/40 hover:bg-red-900/60 border border-red-500/40 text-red-300 hover:text-white font-extrabold text-xs rounded-xl transition flex items-center justify-center gap-2"
                                >
                                    <span>🚪</span> Logout Discord
                                </button>
                            </div>
                        )}
                    </aside>

                    {/* RIGHT MAIN SECTION */}
                    <main className="flex-1 p-6 relative">
                        
                        <div className="absolute top-0 right-0 w-80 h-72 pointer-events-none opacity-80 z-0">
                            <Interactive3DCharacter />
                        </div>

                        {/* Top Header */}
                        <header className="flex flex-wrap items-center justify-between gap-4 p-5 bg-[#12121c]/90 backdrop-blur-md rounded-2xl border border-pink-500/30 shadow-2xl mb-8 relative z-10">
                            <div>
                                <h1 className="text-xl font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-pink-300 via-purple-400 to-pink-500">
                                    MASTER DASHBOARD CONTROL
                                </h1>
                                <p className="text-xs text-gray-400">Manage bots, Auto-Join filters & Crypto Subscriptions</p>
                            </div>

                            <div className="flex items-center gap-3">
                                {discordUser ? (
                                    <div className="flex items-center gap-3 bg-pink-950/60 border border-pink-500/40 px-4 py-2 rounded-xl shadow-lg">
                                        <img src={discordUser.avatar} className="w-8 h-8 rounded-full border border-pink-400" />
                                        <div className="text-left">
                                            <p className="text-xs font-bold text-pink-200">{discordUser.username}</p>
                                            <p className="text-[10px] text-emerald-400 font-bold">Balance: ${walletBalance.toFixed(2)} USD</p>
                                        </div>
                                        <button 
                                            onClick={() => setDiscordUser(null)}
                                            className="ml-2 px-2.5 py-1 bg-red-600/20 hover:bg-red-600 text-red-300 hover:text-white border border-red-500/40 rounded-lg text-[10px] font-bold transition"
                                        >
                                            Logout 🚪
                                        </button>
                                    </div>
                                ) : (
                                    <button 
                                        onClick={handleDiscordOAuth}
                                        className="px-4 py-2.5 bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-extrabold text-xs rounded-xl shadow-lg transition flex items-center gap-2"
                                    >
                                        <span>👾</span> Connect Discord.com
                                    </button>
                                )}
                            </div>
                        </header>

                        {/* KEY TIMER & DURATION CONTROL CARD */}
                        <div className="bg-[#12121c] p-6 rounded-2xl border border-pink-500/50 shadow-2xl mb-8 relative z-10">
                            <div className="flex flex-wrap justify-between items-center gap-4 mb-4 border-b border-pink-900/30 pb-4">
                                <div>
                                    <span className="text-xs font-bold text-pink-400 uppercase tracking-widest block">🔑 ACTIVE KEY TIMER & DURATION</span>
                                    <p className="text-2xl font-black font-mono text-white mt-1">
                                        {formatTime(keyTimer)}
                                    </p>
                                    <p className="text-xs text-gray-400 mt-0.5">Key: <span className="font-mono text-pink-300">{activeKey}</span></p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-gray-300">Extend Key:</span>
                                    <button onClick={() => extendKeyTime(1)} className="px-3 py-1.5 bg-pink-900/40 hover:bg-pink-700 border border-pink-500/50 text-pink-200 text-xs font-bold rounded-lg transition">+1h</button>
                                    <button onClick={() => extendKeyTime(2)} className="px-3 py-1.5 bg-pink-900/40 hover:bg-pink-700 border border-pink-500/50 text-pink-200 text-xs font-bold rounded-lg transition">+2h</button>
                                    <button onClick={() => extendKeyTime(6)} className="px-3 py-1.5 bg-pink-900/40 hover:bg-pink-700 border border-pink-500/50 text-pink-200 text-xs font-bold rounded-lg transition">+6h</button>
                                    <button onClick={() => extendKeyTime(12)} className="px-3 py-1.5 bg-pink-900/40 hover:bg-pink-700 border border-pink-500/50 text-pink-200 text-xs font-bold rounded-lg transition">+12h</button>
                                    <button onClick={() => extendKeyTime(24)} className="px-3 py-1.5 bg-pink-600 hover:bg-pink-500 text-white text-xs font-bold rounded-lg transition shadow-lg">+24h</button>
                                </div>
                            </div>
                            <div className="w-full bg-[#08080d] h-2.5 rounded-full overflow-hidden border border-pink-900/40">
                                <div 
                                    className="bg-gradient-to-r from-pink-500 to-purple-500 h-full transition-all duration-1000"
                                    style={{ width: `${Math.min(100, (keyTimer / 86400) * 100)}%` }}
                                ></div>
                            </div>
                        </div>

                        {/* Main Stats Row */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8 relative z-10">
                            <div className="bg-[#12121c] p-5 rounded-2xl border border-gray-800 shadow-lg">
                                <span className="text-xs text-gray-400 uppercase font-semibold">Bots Online</span>
                                <p className="text-3xl font-extrabold text-white mt-1">{stats.clients}</p>
                            </div>
                            <div className="bg-[#12121c] p-5 rounded-2xl border border-gray-800 shadow-lg">
                                <span className="text-xs text-gray-400 uppercase font-semibold">Total Steals</span>
                                <p className="text-3xl font-extrabold text-purple-400 mt-1">{stats.total_steals}</p>
                            </div>
                            <div className="bg-[#12121c] p-5 rounded-2xl border border-gray-800 shadow-lg">
                                <span className="text-xs text-gray-400 uppercase font-semibold">OG / Secret Steals</span>
                                <p className="text-3xl font-extrabold text-pink-500 mt-1">{stats.og_steals}</p>
                            </div>
                            <div className="bg-[#12121c] p-5 rounded-2xl border border-gray-800 shadow-lg">
                                <span className="text-xs text-gray-400 uppercase font-semibold">Active Plan</span>
                                <p className="text-3xl font-extrabold text-emerald-400 mt-1">{activePlan}</p>
                            </div>
                        </div>

                        {/* Subscription Plans Grid */}
                        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2 relative z-10">
                            <span>💎</span> Select Key Duration & Subscription Plan (1h to 24h)
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8 relative z-10">
                            {/* Farmer */}
                            <div className="bg-[#12121c] p-6 rounded-2xl border border-gray-800 hover:border-emerald-500/50 transition flex flex-col justify-between">
                                <div>
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-bold text-emerald-400">🌾 FARMER</h3>
                                        <span className="text-xs px-2 py-1 bg-emerald-500/10 text-emerald-300 rounded-md font-bold">$2/hr</span>
                                    </div>
                                    <ul className="text-xs text-gray-300 space-y-2 mb-4">
                                        <li>• Max Value: <b>1.5B</b></li>
                                        <li>• Excluded: <b>Dragons, OG, Signor Carapace</b></li>
                                        <li>• Included: <b>Garama, Capitano, Burguro</b></li>
                                    </ul>
                                </div>
                                <button 
                                    onClick={() => { setSelectedCrypto("BTC"); setShowPaymentModal(true); }}
                                    className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition"
                                >
                                    Get Farmer Key
                                </button>
                            </div>

                            {/* Lowlight */}
                            <div className="bg-[#12121c] p-6 rounded-2xl border border-gray-800 hover:border-blue-500/50 transition flex flex-col justify-between">
                                <div>
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-bold text-blue-400">💡 LOWLIGHT</h3>
                                        <span className="text-xs px-2 py-1 bg-blue-500/10 text-blue-300 rounded-md font-bold">$4/hr</span>
                                    </div>
                                    <ul className="text-xs text-gray-300 space-y-2 mb-4">
                                        <li>• Max Value: <b>1.5B</b></li>
                                        <li>• Low Value Filtered Logs</li>
                                        <li>• Fast Teleport Engine</li>
                                    </ul>
                                </div>
                                <button 
                                    onClick={() => { setSelectedCrypto("ETH"); setShowPaymentModal(true); }}
                                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl transition"
                                >
                                    Get Lowlight Key
                                </button>
                            </div>

                            {/* Pro */}
                            <div className="bg-[#12121c] p-6 rounded-2xl border border-pink-500/40 hover:border-pink-400 transition flex flex-col justify-between relative overflow-hidden">
                                <div className="absolute -right-6 -top-6 bg-pink-600 text-[10px] font-bold text-white px-8 py-1 rotate-45 uppercase">Popular</div>
                                <div>
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-bold text-pink-400">⚡ PRO</h3>
                                        <span className="text-xs px-2 py-1 bg-pink-500/10 text-pink-300 rounded-md font-bold">$8/hr</span>
                                    </div>
                                    <ul className="text-xs text-gray-300 space-y-2 mb-4">
                                        <li>• <b>1 OF 1 Rare Steals</b></li>
                                        <li>• Included: <b>Dragons & OG Secrets</b></li>
                                        <li>• Ultra Fast Teleporting</li>
                                    </ul>
                                </div>
                                <button 
                                    onClick={() => { setSelectedCrypto("USDT"); setShowPaymentModal(true); }}
                                    className="w-full py-2.5 bg-pink-600 hover:bg-pink-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-pink-900/40"
                                >
                                    Get Pro Key
                                </button>
                            </div>

                            {/* Ultralight */}
                            <div className="bg-[#12121c] p-6 rounded-2xl border border-purple-500/40 hover:border-purple-400 transition flex flex-col justify-between">
                                <div>
                                    <div className="flex justify-between items-center mb-3">
                                        <h3 className="text-lg font-bold text-purple-400">🚀 ULTRALIGHT</h3>
                                        <span className="text-xs px-2 py-1 bg-purple-500/10 text-purple-300 rounded-md font-bold">$12/hr</span>
                                    </div>
                                    <ul className="text-xs text-gray-300 space-y-2 mb-4">
                                        <li>• <b>Unlimited All Brainrots</b></li>
                                        <li>• 100% Custom Whitelist Filter</li>
                                        <li>• VIP Priority Support</li>
                                    </ul>
                                </div>
                                <button 
                                    onClick={() => { setSelectedCrypto("SOL"); setShowPaymentModal(true); }}
                                    className="w-full py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white text-xs font-bold rounded-xl transition"
                                >
                                    Get Ultralight Key
                                </button>
                            </div>
                        </div>

                    </main>

                    {/* Crypto Payment Modal */}
                    {showPaymentModal && (
                        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                            <div className="bg-[#12121c] border border-pink-500/30 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
                                <button onClick={() => setShowPaymentModal(false)} className="absolute top-4 right-4 text-gray-400 hover:text-white font-bold">✕</button>
                                <h3 className="text-lg font-bold text-white mb-2">💳 Checkout & Select Key Duration (1h to 24h)</h3>
                                
                                <div className="mb-4">
                                    <label className="text-xs font-bold text-gray-300 block mb-1">Select Duration (Hours):</label>
                                    <select 
                                        value={selectedHours} 
                                        onChange={(e) => setSelectedHours(Number(e.target.value))}
                                        className="w-full bg-[#08080d] border border-pink-500/40 rounded-xl p-2.5 text-xs text-white focus:outline-none"
                                    >
                                        <option value={1}>1 Hour Key</option>
                                        <option value={2}>2 Hours Key</option>
                                        <option value={4}>4 Hours Key</option>
                                        <option value={6}>6 Hours Key</option>
                                        <option value={12}>12 Hours Key</option>
                                        <option value={24}>24 Hours Key (Full Day)</option>
                                    </select>
                                </div>

                                <p className="text-xs text-gray-400 mb-2">Choose Crypto for Payment:</p>
                                <div className="grid grid-cols-4 gap-2 mb-4">
                                    {["BTC", "ETH", "USDT", "SOL"].map(c => (
                                        <button 
                                            key={c}
                                            onClick={() => setSelectedCrypto(c)}
                                            className={`py-2 text-xs font-bold rounded-xl border ${selectedCrypto === c ? 'bg-pink-600 border-pink-400 text-white' : 'bg-[#090910] border-gray-800 text-gray-400'}`}
                                        >
                                            {c}
                                        </button>
                                    ))}
                                </div>

                                <div className="bg-[#08080d] p-3 rounded-xl border border-gray-800 mb-4 text-center">
                                    <p className="text-[10px] text-gray-400 mb-1">Deposit Address ({selectedCrypto}) :</p>
                                    <p className="text-xs font-mono font-bold text-pink-300 break-all select-all">
                                        {selectedCrypto === 'BTC' && '1AjSABMasterCryptoBtcAddress9999'}
                                        {selectedCrypto === 'ETH' && '0xAjSABMasterCryptoEthAddress9999'}
                                        {selectedCrypto === 'USDT' && '0xAjSABMasterCryptoUsdtAddress9999'}
                                        {selectedCrypto === 'SOL' && 'SolAjSABMasterCryptoSolAddress9999'}
                                    </p>
                                </div>

                                <button 
                                    onClick={() => simulateCryptoPayment("PRO", 8.00)}
                                    className="w-full py-3 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white font-bold text-xs rounded-xl shadow-lg transition"
                                >
                                    ✅ Complete Purchase ({selectedHours}h Key)
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get('/', handle_dashboard)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_post('/api/payment_notify', handle_payment_notify)
    app.router.add_post('/api/add_wallet', handle_add_wallet)

    print(f"[+] Server online on port {port} (Combined HTTP Dashboard & WebSocket Master)")
    web.run_app(app, host="0.0.0.0", port=port)
