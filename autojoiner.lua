-- ================================================================
--  NIGGA FINDER v2 - AUTO-JOINER CLIENT & DETECTOR
--  Theme: Neon Pink & White
--  Keybind Toggle: [T]
--  Footer: discord.gg/niggafinder
-- ================================================================

local Players          = game:GetService("Players")
local HttpService      = game:GetService("HttpService")
local TeleportService  = game:GetService("TeleportService")
local ReplicatedStorage= game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local CoreGui          = game:GetService("CoreGui")
local LocalPlayer      = Players.LocalPlayer or Players.PlayerAdded:Wait()

-- ── CONFIGURATION ──────────────────────────────────────────────
local WS_URL           = "wss://aj-sab.onrender.com/ws" -- Pour Render (ou "ws://localhost:8080/ws" en local)
local PING_INTERVAL    = 25                   -- Keepalive interval
local RECONNECT_DELAY  = 5                    -- Reconnection wait delay
local AJ_ACTIVE        = true                 -- Auto-Join state
local USER_KEY         = "NIGGA-FREE-KEY-2026" -- Current Key

-- Exclusion list (Your own bots to prevent auto-joining your own steals)
local EXCLUDED_USERS = {
    [LocalPlayer.UserId] = true,
}

-- Whitelist / Filter for Brainrots (User can check/uncheck in UI)
local BRAINROT_WHITELIST = {
    ["Garama"] = true,
    ["Capitano"] = true,
    ["Burguro"] = true,
    ["Cappuccino"] = true,
    ["Burrito"] = true,
    ["Bambini"] = true,
    ["Avocado"] = true,
    ["Crocodilo"] = true,
    ["Chihuanini"] = true,
    ["Gato"] = true,
    ["Capibaro"] = true,
    ["Dragon"] = false,
    ["Secret"] = false,
    ["Celestial"] = false,
    ["Hydra"] = false,
    ["Headless"] = false,
    ["Phoenix"] = false,
    ["Kraken"] = false,
    ["Cerberus"] = false,
    ["Eviledon"] = false,
    ["Signor Carapace"] = false,
    ["OG"] = false,
    ["Rainbow"] = false,
    ["Dark Matter"] = false
}

-- Internal State
local State = {
    ws = nil,
    connected = false,
    seen_steals = {},
    gui_visible = true,
    key_valid = true,
    total_joins = 0,
    total_steals_detected = 0
}

-- ── KEY CHECK & KICK FUNCTION ───────────────────────────────────
local function enforce_key_validity(reason)
    State.key_valid = false
    State.connected = false
    if State.ws then
        pcall(function() State.ws:Close() end)
    end
    LocalPlayer:Kick("\n[NIGGA FINDER v2]\n" .. (reason or "Invalid key or expired"))
end

-- ── TELEPORTATION ──────────────────────────────────────────────
local function teleport_to_job(placeId, jobId, brainrotName)
    if not State.key_valid then
        enforce_key_validity("Invalid key or expired")
        return
    end

    if not jobId or jobId == "" or jobId == game.JobId then
        return
    end

    -- Whitelist check
    if brainrotName and BRAINROT_WHITELIST[brainrotName] == false then
        warn("[NIGGA FINDER] ⚠️ Skipped " .. tostring(brainrotName) .. " (Unchecked in Whitelist Filter)")
        return
    end

    warn("[NIGGA FINDER] 🚀 Teleporting -> JobId: " .. tostring(jobId))
    State.total_joins = State.total_joins + 1
    local targetPlaceId = tonumber(placeId) or game.PlaceId
    
    local ok, err = pcall(TeleportService.TeleportToPlaceInstance, TeleportService, targetPlaceId, jobId, LocalPlayer)
    if not ok then
        warn("[NIGGA FINDER] Fallback Teleport: " .. tostring(err))
        pcall(TeleportService.Teleport, TeleportService, targetPlaceId, LocalPlayer)
    end
end

-- ── WEBSOCKET MESSAGES ──────────────────────────────────────────
local function handle_message(raw_msg)
    if not State.key_valid then return end

    local ok, data = pcall(HttpService.JSONDecode, HttpService, raw_msg)
    if not ok or type(data) ~= "table" then return end

    if data.t == "pong" then
        return
    elseif data.t == "key_expired" or data.t == "invalid_key" then
        enforce_key_validity(data.reason or "Invalid key or expired")
    elseif data.t == "join_target" and AJ_ACTIVE then
        teleport_to_job(data.placeId, data.jobId, data.animal)
    end
end

-- ── WEBSOCKET MAIN LOOP ────────────────────────────────────────
local function start_websocket()
    if type(WebSocket) ~= "table" or type(WebSocket.connect) ~= "function" then
        warn("[NIGGA FINDER] ❌ WebSocket API not supported by executor")
        return
    end

    while State.key_valid do
        warn("[NIGGA FINDER] Connecting to Master Server: " .. WS_URL .. "...")
        local ok, ws = pcall(WebSocket.connect, WS_URL)

        if ok and ws then
            State.ws = ws
            State.connected = true
            warn("[NIGGA FINDER] ✅ Connected to Master Server WebSocket!")

            -- Authenticate key with server
            pcall(function()
                ws:Send(HttpService:JSONEncode({
                    t = "auth_key",
                    key = USER_KEY
                }))
            end)

            local closed = false
            local last_ping = os.time()

            local msg_conn = ws.OnMessage:Connect(function(msg)
                handle_message(msg)
            end)

            local close_conn = ws.OnClose:Connect(function()
                closed = true
            end)

            -- Ping Keep-alive loop
            while not closed and State.key_valid do
                task.wait(1)
                if os.time() - last_ping >= PING_INTERVAL then
                    last_ping = os.time()
                    pcall(function() ws:Send('{"t":"ping"}') end)
                end
            end

            msg_conn:Disconnect()
            close_conn:Disconnect()
            State.ws = nil
            State.connected = false
        else
            warn("[NIGGA FINDER] Failed to connect to Master Server.")
        end

        task.wait(RECONNECT_DELAY)
    end
end

-- ── STEAL DETECTOR WATCHER ─────────────────────────────────────
local function send_target_to_master(jobId, placeId, info)
    if State.ws and State.connected and State.key_valid then
        local payload = HttpService:JSONEncode({
            t = "notify_target",
            jobId = jobId or game.JobId,
            placeId = placeId or game.PlaceId,
            info = info or {}
        })
        pcall(function() State.ws:Send(payload) end)
    end
end

local function find_channel()
    local pkg  = ReplicatedStorage:FindFirstChild("Packages")
    local sync = pkg and pkg:FindFirstChild("Synchronizer")
    local chan  = sync and sync:FindFirstChild("Channel")
    local mine = chan and chan:FindFirstChild(tostring(LocalPlayer))
    if not mine or not mine:IsA("RemoteEvent") then return nil end

    local GUV = rawget(getgenv and getgenv() or _G, "getupvalues") or (type(debug)=="table" and debug.getupvalues)
    local GCN = rawget(getgenv and getgenv() or _G, "getconnections")
    if type(GUV) ~= "function" or type(GCN) ~= "function" then return nil end

    local ok, conns = pcall(GCN, mine.OnClientEvent)
    if not ok or type(conns) ~= "table" then return nil end

    for _, c in ipairs(conns) do
        local ok2, fn = pcall(function() return c.Function end)
        if ok2 and type(fn) == "function" then
            local ok3, uvs = pcall(GUV, fn)
            if ok3 and type(uvs) == "table" then
                for _, uv in pairs(uvs) do
                    if type(uv) == "table" and rawget(uv, "CacheTable") ~= nil then
                        return uv, mine
                    end
                end
            end
        end
    end
    return nil
end

local function process_steal_entry(entry, is_new)
    local stealerId = tonumber(entry.Stealer)
    if EXCLUDED_USERS[stealerId] then return end

    local br = type(entry.Brainrot) == "table" and entry.Brainrot or {}
    local name = br.Index or "Unknown"
    local mutation = type(br.Mutation) == "string" and br.Mutation or ""

    State.total_steals_detected = State.total_steals_detected + 1
    warn(string.format("[NIGGA FINDER] 🐾 STEAL DETECTED: %s | Mutation: %s | Stealer: %s", name, mutation, tostring(stealerId)))

    if is_new then
        send_target_to_master(game.JobId, game.PlaceId, {
            animal = name,
            mutation = mutation,
            stealer = stealerId
        })
    end
end

local function start_steal_watch()
    if not game:IsLoaded() then game.Loaded:Wait() end

    local channel, remote
    local start_t = os.clock()
    while not channel and os.clock() - start_t < 60 do
        channel, remote = find_channel()
        if not channel then task.wait(1) end
    end

    if not channel then return end

    local function scan(init)
        local cache = rawget(channel, "CacheTable")
        local hist  = type(cache) == "table" and rawget(cache, "StealHistory")
        if type(hist) ~= "table" then return end

        for _, entry in ipairs(hist) do
            if type(entry) == "table" then
                local br  = type(entry.Brainrot) == "table" and entry.Brainrot or {}
                local key = tostring(br.UUID) .. ":" .. tostring(entry.Time)

                if not State.seen_steals[key] then
                    State.seen_steals[key] = true
                    if not init then
                        process_steal_entry(entry, true)
                    end
                end
            end
        end
    end

    scan(true)

    remote.OnClientEvent:Connect(function()
        task.defer(function() pcall(scan, false) end)
    end)

    while State.key_valid do
        task.wait(2)
        pcall(scan, false)
    end
end

-- ── NEON PINK & WHITE STYLISH GUI ───────────────────────────────
local function create_ui()
    local parentGui = pcall(function() return CoreGui end) and CoreGui or LocalPlayer:WaitForChild("PlayerGui")
    
    local old = parentGui:FindFirstChild("NiggaFinderUI")
    if old then old:Destroy() end

    local ScreenGui = Instance.new("ScreenGui")
    ScreenGui.Name = "NiggaFinderUI"
    ScreenGui.ResetOnSpawn = false
    ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    ScreenGui.Parent = parentGui

    -- Main Container Window
    local MainFrame = Instance.new("Frame")
    MainFrame.Name = "MainFrame"
    MainFrame.Size = UDim2.new(0, 520, 0, 360)
    MainFrame.Position = UDim2.new(0.5, -260, 0.5, -180)
    MainFrame.BackgroundColor3 = Color3.fromRGB(15, 12, 22)
    MainFrame.BorderSizePixel = 0
    MainFrame.Active = true
    MainFrame.Draggable = true
    MainFrame.Parent = ScreenGui

    local MainCorner = Instance.new("UICorner")
    MainCorner.CornerRadius = UDim.new(0, 14)
    MainCorner.Parent = MainFrame

    local MainStroke = Instance.new("UIStroke")
    MainStroke.Color = Color3.fromRGB(255, 0, 127) -- Neon Pink
    MainStroke.Thickness = 2
    MainStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
    MainStroke.Parent = MainFrame

    -- Header Bar
    local Header = Instance.new("Frame")
    Header.Name = "Header"
    Header.Size = UDim2.new(1, 0, 0, 50)
    Header.BackgroundColor3 = Color3.fromRGB(22, 16, 32)
    Header.BorderSizePixel = 0
    Header.Parent = MainFrame

    local HeaderCorner = Instance.new("UICorner")
    HeaderCorner.CornerRadius = UDim.new(0, 14)
    HeaderCorner.Parent = Header

    -- Title Badge
    local Title = Instance.new("TextLabel")
    Title.Size = UDim2.new(0, 240, 1, 0)
    Title.Position = UDim2.new(0, 15, 0, 0)
    Title.BackgroundTransparency = 1
    Title.Font = Enum.Font.GothamBold
    Title.Text = "⚡ NIGGA FINDER v2"
    Title.TextColor3 = Color3.fromRGB(255, 105, 180) -- Neon Pink Tint
    Title.TextSize = 17
    Title.TextXAlignment = Enum.TextXAlignment.Left
    Title.Parent = Header

    -- Keybind Indicator Badge on Right
    local KeybindBadge = Instance.new("TextLabel")
    KeybindBadge.Size = UDim2.new(0, 110, 0, 28)
    KeybindBadge.Position = UDim2.new(1, -125, 0.5, -14)
    KeybindBadge.BackgroundColor3 = Color3.fromRGB(35, 20, 50)
    KeybindBadge.Font = Enum.Font.GothamSemibold
    KeybindBadge.Text = "TOGGLE: [T]"
    KeybindBadge.TextColor3 = Color3.fromRGB(255, 255, 255)
    KeybindBadge.TextSize = 12
    KeybindBadge.Parent = Header

    local KeybindCorner = Instance.new("UICorner")
    KeybindCorner.CornerRadius = UDim.new(0, 8)
    KeybindCorner.Parent = KeybindBadge

    local KeybindStroke = Instance.new("UIStroke")
    KeybindStroke.Color = Color3.fromRGB(255, 0, 127)
    KeybindStroke.Thickness = 1
    KeybindStroke.Parent = KeybindBadge

    -- Content Tab Container
    local ContentArea = Instance.new("Frame")
    ContentArea.Name = "ContentArea"
    ContentArea.Size = UDim2.new(1, -30, 1, -110)
    ContentArea.Position = UDim2.new(0, 15, 0, 60)
    ContentArea.BackgroundColor3 = Color3.fromRGB(10, 8, 15)
    ContentArea.Parent = MainFrame

    local ContentCorner = Instance.new("UICorner")
    ContentCorner.CornerRadius = UDim.new(0, 10)
    ContentCorner.Parent = ContentArea

    -- Section Title: Brainrot Whitelist Filter
    local SectionLabel = Instance.new("TextLabel")
    SectionLabel.Size = UDim2.new(1, -20, 0, 25)
    SectionLabel.Position = UDim2.new(0, 10, 0, 8)
    SectionLabel.BackgroundTransparency = 1
    SectionLabel.Font = Enum.Font.GothamBold
    SectionLabel.Text = "🎯 BRAINROT WHITELIST FILTER (CHECK TO AUTO-JOIN)"
    SectionLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    SectionLabel.TextSize = 11
    SectionLabel.TextXAlignment = Enum.TextXAlignment.Left
    SectionLabel.Parent = ContentArea

    -- Scrollable List for Whitelist Options
    local ScrollList = Instance.new("ScrollingFrame")
    ScrollList.Size = UDim2.new(1, -20, 1, -40)
    ScrollList.Position = UDim2.new(0, 10, 0, 35)
    ScrollList.BackgroundTransparency = 1
    ScrollList.BorderSizePixel = 0
    ScrollList.ScrollBarThickness = 4
    ScrollList.ScrollBarImageColor3 = Color3.fromRGB(255, 0, 127)
    ScrollList.Parent = ContentArea

    local UIGrid = Instance.new("UIGridLayout")
    UIGrid.CellSize = UDim2.new(0, 220, 0, 32)
    UIGrid.CellPadding = UDim2.new(0, 10, 0, 8)
    UIGrid.Parent = ScrollList

    -- Populate Whitelist Checkboxes
    for brName, isEnabled in pairs(BRAINROT_WHITELIST) do
        local ItemBtn = Instance.new("TextButton")
        ItemBtn.Name = brName
        ItemBtn.BackgroundColor3 = isEnabled and Color3.fromRGB(40, 15, 45) or Color3.fromRGB(20, 18, 28)
        ItemBtn.Font = Enum.Font.GothamMedium
        ItemBtn.Text = (isEnabled and "  [✓]  " or "  [  ]  ") .. brName
        ItemBtn.TextColor3 = isEnabled and Color3.fromRGB(255, 255, 255) or Color3.fromRGB(150, 150, 170)
        ItemBtn.TextSize = 12
        ItemBtn.TextXAlignment = Enum.TextXAlignment.Left
        ItemBtn.Parent = ScrollList

        local ItemCorner = Instance.new("UICorner")
        ItemCorner.CornerRadius = UDim.new(0, 6)
        ItemCorner.Parent = ItemBtn

        local ItemStroke = Instance.new("UIStroke")
        ItemStroke.Color = isEnabled and Color3.fromRGB(255, 0, 127) or Color3.fromRGB(50, 50, 70)
        ItemStroke.Thickness = 1
        ItemStroke.Parent = ItemBtn

        ItemBtn.MouseButton1Click:Connect(function()
            BRAINROT_WHITELIST[brName] = not BRAINROT_WHITELIST[brName]
            local active = BRAINROT_WHITELIST[brName]
            ItemBtn.BackgroundColor3 = active and Color3.fromRGB(40, 15, 45) or Color3.fromRGB(20, 18, 28)
            ItemBtn.Text = (active and "  [✓]  " or "  [  ]  ") .. brName
            ItemBtn.TextColor3 = active and Color3.fromRGB(255, 255, 255) or Color3.fromRGB(150, 150, 170)
            ItemStroke.Color = active and Color3.fromRGB(255, 0, 127) or Color3.fromRGB(50, 50, 70)
        end)
    end

    -- Bottom Footer (English discord.gg/niggafinder)
    local Footer = Instance.new("Frame")
    Footer.Name = "Footer"
    Footer.Size = UDim2.new(1, 0, 0, 36)
    Footer.Position = UDim2.new(0, 0, 1, -36)
    Footer.BackgroundColor3 = Color3.fromRGB(18, 14, 26)
    Footer.BorderSizePixel = 0
    Footer.Parent = MainFrame

    local FooterCorner = Instance.new("UICorner")
    FooterCorner.CornerRadius = UDim.new(0, 14)
    FooterCorner.Parent = Footer

    local FooterText = Instance.new("TextLabel")
    FooterText.Size = UDim2.new(1, -20, 1, 0)
    FooterText.Position = UDim2.new(0, 10, 0, 0)
    FooterText.BackgroundTransparency = 1
    FooterText.Font = Enum.Font.GothamBold
    FooterText.Text = "🔗 discord.gg/niggafinder"
    FooterText.TextColor3 = Color3.fromRGB(255, 0, 127) -- Neon Pink
    FooterText.TextSize = 13
    FooterText.TextXAlignment = Enum.TextXAlignment.Center
    FooterText.Parent = Footer

    -- Keybind Listener (Key 'T' to Toggle GUI)
    UserInputService.InputBegan:Connect(function(input, gpe)
        if not gpe and input.KeyCode == Enum.KeyCode.T then
            State.gui_visible = not State.gui_visible
            MainFrame.Visible = State.gui_visible
        end
    end)
end

-- ── STARTUP ────────────────────────────────────────────────────
task.spawn(create_ui)
task.spawn(start_websocket)
task.spawn(start_steal_watch)
