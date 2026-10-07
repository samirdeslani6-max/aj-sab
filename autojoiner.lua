-- ================================================================
--  NIGGA FINDER v2 - ULTRA CLEAN AUTO-JOINER
--  Theme: Dark Sleek Glassmorphic Nigga Finder UI
--  Keybind Toggle: [T]
--  Footer: discord.gg/niggafinder
-- ================================================================

local Players          = game:GetService("Players")
local HttpService      = game:GetService("HttpService")
local TeleportService  = game:GetService("TeleportService")
local ReplicatedStorage= game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local TweenService     = game:GetService("TweenService")
local CoreGui          = game:GetService("CoreGui")
local LocalPlayer      = Players.LocalPlayer or Players.PlayerAdded:Wait()

-- ── CONFIGURATION ──────────────────────────────────────────────
local WS_URL           = "wss://aj-sab.onrender.com/ws"
local PING_INTERVAL    = 25
local RECONNECT_DELAY  = 5

local CONFIG = {
    AutoJoinActive = true,
    SelectedNode   = "Madrid (Spain - Live)",
    SelectedRegion = "ES",
    UserKey        = "NIGGA-PRO-2026",
    SoundAlert     = true
}

-- Exclusion list (Your own bots to prevent auto-joining your own steals)
local EXCLUDED_USERS = {
    [LocalPlayer.UserId] = true,
}

-- Whitelist / Filter for Brainrots
local BRAINROT_WHITELIST = {
    ["Garama"]            = true,
    ["Capitano"]          = true,
    ["Burguro"]           = true,
    ["Cappuccino"]        = true,
    ["Burrito"]           = true,
    ["Bambini"]           = true,
    ["Avocado"]           = true,
    ["Crocodilo"]         = true,
    ["Chihuanini"]        = true,
    ["Gato"]              = true,
    ["Capibaro"]          = true,
    ["Dragon"]            = true,
    ["Secret"]            = true,
    ["Celestial"]         = true,
    ["Hydra"]             = true,
    ["Headless"]          = true,
    ["Phoenix"]           = true,
    ["Kraken"]            = true,
    ["Cerberus"]          = true,
    ["Eviledon"]          = true,
    ["Signor Carapace"]   = true,
    ["OG"]                = true,
    ["Rainbow"]           = true,
    ["Dark Matter"]       = true
}

-- Internal Runtime State
local State = {
    ws = nil,
    connected = false,
    seen_steals = {},
    gui_visible = true,
    key_valid = true,
    total_joins = 0,
    total_steals_detected = 0,
    active_tab = "STEALS", -- STEALS, WHITELIST, NODES, SETTINGS
    steals_history = {}
}

-- GUI Global References
local UI = {}

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
local function add_steal_to_log_ui(steal_data)
    table.insert(State.steals_history, 1, steal_data)
    if #State.steals_history > 50 then
        table.remove(State.steals_history)
    end

    if UI.RefreshStealsList then
        UI.RefreshStealsList()
    end
end

local function handle_message(raw_msg)
    if not State.key_valid then return end

    local ok, data = pcall(HttpService.JSONDecode, HttpService, raw_msg)
    if not ok or type(data) ~= "table" then return end

    if data.t == "pong" then
        return
    elseif data.t == "key_expired" or data.t == "invalid_key" then
        enforce_key_validity(data.reason or "Invalid key or expired")
    elseif data.t == "join_target" then
        local steal_info = {
            animal = data.animal or "Target",
            mutation = data.mutation or "Normal",
            jobId = data.jobId or "",
            placeId = data.placeId or game.PlaceId,
            time = os.date("%H:%M:%S")
        }
        add_steal_to_log_ui(steal_info)

        if CONFIG.AutoJoinActive then
            teleport_to_job(data.placeId, data.jobId, data.animal)
        end
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
            if UI.UpdateStatus then UI.UpdateStatus(true) end
            warn("[NIGGA FINDER] ✅ Connected to Master Server WebSocket!")

            pcall(function()
                ws:Send(HttpService:JSONEncode({
                    t = "auth_key",
                    key = CONFIG.UserKey
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
            if UI.UpdateStatus then UI.UpdateStatus(false) end
        else
            if UI.UpdateStatus then UI.UpdateStatus(false) end
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

    local steal_info = {
        animal = name,
        mutation = mutation,
        jobId = game.JobId,
        placeId = game.PlaceId,
        time = os.date("%H:%M:%S")
    }
    add_steal_to_log_ui(steal_info)

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

-- ── ODYSSEY STYLE CLEAN GUI CREATION ────────────────────────────
local function create_ui()
    local parentGui = pcall(function() return CoreGui end) and CoreGui or LocalPlayer:WaitForChild("PlayerGui")
    
    local old = parentGui:FindFirstChild("NiggaFinderUI")
    if old then old:Destroy() end

    local ScreenGui = Instance.new("ScreenGui")
    ScreenGui.Name = "NiggaFinderUI"
    ScreenGui.ResetOnSpawn = false
    ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    ScreenGui.Parent = parentGui

    -- Main Frame (Glassmorphism Dark)
    local MainFrame = Instance.new("Frame")
    MainFrame.Name = "MainFrame"
    MainFrame.Size = UDim2.new(0, 680, 0, 440)
    MainFrame.Position = UDim2.new(0.5, -340, 0.5, -220)
    MainFrame.BackgroundColor3 = Color3.fromRGB(15, 17, 23)
    MainFrame.BorderSizePixel = 0
    MainFrame.Active = true
    MainFrame.Draggable = true
    MainFrame.Parent = ScreenGui

    local MainCorner = Instance.new("UICorner")
    MainCorner.CornerRadius = UDim.new(0, 16)
    MainCorner.Parent = MainFrame

    local MainStroke = Instance.new("UIStroke")
    MainStroke.Color = Color3.fromRGB(35, 42, 60)
    MainStroke.Thickness = 1.5
    MainStroke.Parent = MainFrame

    -- Top Header Bar (Nigga Finder Header Style)
    local Header = Instance.new("Frame")
    Header.Name = "Header"
    Header.Size = UDim2.new(1, 0, 0, 55)
    Header.BackgroundColor3 = Color3.fromRGB(20, 23, 32)
    Header.BorderSizePixel = 0
    Header.Parent = MainFrame

    local HeaderCorner = Instance.new("UICorner")
    HeaderCorner.CornerRadius = UDim.new(0, 16)
    HeaderCorner.Parent = Header

    -- Status Dot & Brand Logo
    local StatusDot = Instance.new("Frame")
    StatusDot.Size = UDim2.new(0, 10, 0, 10)
    StatusDot.Position = UDim2.new(0, 18, 0.5, -5)
    StatusDot.BackgroundColor3 = Color3.fromRGB(46, 204, 113)
    StatusDot.BorderSizePixel = 0
    StatusDot.Parent = Header

    local DotCorner = Instance.new("UICorner")
    DotCorner.CornerRadius = UDim.new(1, 0)
    DotCorner.Parent = StatusDot

    UI.UpdateStatus = function(is_online)
        StatusDot.BackgroundColor3 = is_online and Color3.fromRGB(46, 204, 113) or Color3.fromRGB(231, 76, 60)
    end

    local BrandTitle = Instance.new("TextLabel")
    BrandTitle.Size = UDim2.new(0, 150, 1, 0)
    BrandTitle.Position = UDim2.new(0, 36, 0, 0)
    BrandTitle.BackgroundTransparency = 1
    BrandTitle.Font = Enum.Font.GothamBold
    BrandTitle.Text = "Nigga Finder v2"
    BrandTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
    BrandTitle.TextSize = 16
    BrandTitle.TextXAlignment = Enum.TextXAlignment.Left
    BrandTitle.Parent = Header

    -- VIP Access Badge
    local VipBadge = Instance.new("Frame")
    VipBadge.Size = UDim2.new(0, 115, 0, 28)
    VipBadge.Position = UDim2.new(0, 185, 0.5, -14)
    VipBadge.BackgroundColor3 = Color3.fromRGB(30, 26, 18)
    VipBadge.Parent = Header

    local VipCorner = Instance.new("UICorner")
    VipCorner.CornerRadius = UDim.new(0, 8)
    VipCorner.Parent = VipBadge

    local VipStroke = Instance.new("UIStroke")
    VipStroke.Color = Color3.fromRGB(245, 166, 35)
    VipStroke.Thickness = 1
    VipStroke.Parent = VipBadge

    local VipText = Instance.new("TextLabel")
    VipText.Size = UDim2.new(1, 0, 1, 0)
    VipText.BackgroundTransparency = 1
    VipText.Font = Enum.Font.GothamBold
    VipText.Text = "👑 VIP · Active"
    VipText.TextColor3 = Color3.fromRGB(245, 166, 35)
    VipText.TextSize = 11
    VipText.Parent = VipBadge

    -- Region Flag Badge
    local RegionBtn = Instance.new("TextButton")
    RegionBtn.Size = UDim2.new(0, 75, 0, 28)
    RegionBtn.Position = UDim2.new(0, 310, 0.5, -14)
    RegionBtn.BackgroundColor3 = Color3.fromRGB(26, 30, 42)
    RegionBtn.Font = Enum.Font.GothamBold
    RegionBtn.Text = "🇪🇸 ES"
    RegionBtn.TextColor3 = Color3.fromRGB(200, 210, 230)
    RegionBtn.TextSize = 11
    RegionBtn.Parent = Header

    local RegionCorner = Instance.new("UICorner")
    RegionCorner.CornerRadius = UDim.new(0, 8)
    RegionCorner.Parent = RegionBtn

    -- AutoJoin Toggle Switch
    local AutoJoinBtn = Instance.new("TextButton")
    AutoJoinBtn.Size = UDim2.new(0, 110, 0, 28)
    AutoJoinBtn.Position = UDim2.new(1, -185, 0.5, -14)
    AutoJoinBtn.BackgroundColor3 = CONFIG.AutoJoinActive and Color3.fromRGB(245, 166, 35) or Color3.fromRGB(35, 40, 55)
    AutoJoinBtn.Font = Enum.Font.GothamBold
    AutoJoinBtn.Text = CONFIG.AutoJoinActive and "➔| MultiJoin [ON]" or "➔| MultiJoin [OFF]"
    AutoJoinBtn.TextColor3 = CONFIG.AutoJoinActive and Color3.fromRGB(15, 17, 23) or Color3.fromRGB(180, 190, 210)
    AutoJoinBtn.TextSize = 11
    AutoJoinBtn.Parent = Header

    local AjCorner = Instance.new("UICorner")
    AjCorner.CornerRadius = UDim.new(0, 8)
    AjCorner.Parent = AutoJoinBtn

    AutoJoinBtn.MouseButton1Click:Connect(function()
        CONFIG.AutoJoinActive = not CONFIG.AutoJoinActive
        AutoJoinBtn.BackgroundColor3 = CONFIG.AutoJoinActive and Color3.fromRGB(245, 166, 35) or Color3.fromRGB(35, 40, 55)
        AutoJoinBtn.Text = CONFIG.AutoJoinActive and "➔| MultiJoin [ON]" or "➔| MultiJoin [OFF]"
        AutoJoinBtn.TextColor3 = CONFIG.AutoJoinActive and Color3.fromRGB(15, 17, 23) or Color3.fromRGB(180, 190, 210)
    end)

    -- Keybind Toggle Badge (Right side)
    local KeyBadge = Instance.new("TextLabel")
    KeyBadge.Size = UDim2.new(0, 60, 0, 28)
    KeyBadge.Position = UDim2.new(1, -70, 0.5, -14)
    KeyBadge.BackgroundColor3 = Color3.fromRGB(26, 30, 42)
    KeyBadge.Font = Enum.Font.GothamBold
    KeyBadge.Text = "[ T ]"
    KeyBadge.TextColor3 = Color3.fromRGB(140, 150, 175)
    KeyBadge.TextSize = 11
    KeyBadge.Parent = Header

    local KeyCorner = Instance.new("UICorner")
    KeyCorner.CornerRadius = UDim.new(0, 8)
    KeyCorner.Parent = KeyBadge

    -- Tab Navigation Container
    local TabContainer = Instance.new("Frame")
    TabContainer.Size = UDim2.new(1, -30, 0, 35)
    TabContainer.Position = UDim2.new(0, 15, 0, 65)
    TabContainer.BackgroundTransparency = 1
    TabContainer.Parent = MainFrame

    local Tabs = {
        { id = "STEALS", label = "📡 Live Steals Feed" },
        { id = "WHITELIST", label = "🎯 Target Whitelist" },
        { id = "NODES", label = "🌐 Log Server Nodes" }
    }

    local TabButtons = {}

    -- Content Pages Container
    local PageContainer = Instance.new("Frame")
    PageContainer.Size = UDim2.new(1, -30, 1, -150)
    PageContainer.Position = UDim2.new(0, 15, 0, 105)
    PageContainer.BackgroundColor3 = Color3.fromRGB(20, 23, 32)
    PageContainer.BorderSizePixel = 0
    PageContainer.Parent = MainFrame

    local PageCorner = Instance.new("UICorner")
    PageCorner.CornerRadius = UDim.new(0, 12)
    PageCorner.Parent = PageContainer

    -- Page 1: Live Steals Feed
    local StealsPage = Instance.new("ScrollingFrame")
    StealsPage.Size = UDim2.new(1, -20, 1, -20)
    StealsPage.Position = UDim2.new(0, 10, 0, 10)
    StealsPage.BackgroundTransparency = 1
    StealsPage.BorderSizePixel = 0
    StealsPage.ScrollBarThickness = 4
    StealsPage.ScrollBarImageColor3 = Color3.fromRGB(245, 166, 35)
    StealsPage.Parent = PageContainer

    local StealsLayout = Instance.new("UIListLayout")
    StealsLayout.SortOrder = Enum.SortOrder.LayoutOrder
    StealsLayout.Padding = UDim.new(0, 8)
    StealsLayout.Parent = StealsPage

    UI.RefreshStealsList = function()
        for _, child in ipairs(StealsPage:GetChildren()) do
            if child:IsA("Frame") then child:Destroy() end
        end

        if #State.steals_history == 0 then
            local EmptyLabel = Instance.new("TextLabel")
            EmptyLabel.Size = UDim2.new(1, 0, 0, 150)
            EmptyLabel.BackgroundTransparency = 1
            EmptyLabel.Font = Enum.Font.GothamMedium
            EmptyLabel.Text = "📡 Waiting for live steals from WebSocket bots...\nDetected targets will populate in real-time here."
            EmptyLabel.TextColor3 = Color3.fromRGB(120, 130, 155)
            EmptyLabel.TextSize = 12
            EmptyLabel.Parent = StealsPage
            return
        end

        for idx, item in ipairs(State.steals_history) do
            local Card = Instance.new("Frame")
            Card.Size = UDim2.new(1, -5, 0, 42)
            Card.BackgroundColor3 = Color3.fromRGB(26, 30, 42)
            Card.BorderSizePixel = 0
            Card.LayoutOrder = idx
            Card.Parent = StealsPage

            local CardCorner = Instance.new("UICorner")
            CardCorner.CornerRadius = UDim.new(0, 8)
            CardCorner.Parent = Card

            local ItemInfo = Instance.new("TextLabel")
            ItemInfo.Size = UDim2.new(1, -120, 1, 0)
            ItemInfo.Position = UDim2.new(0, 12, 0, 0)
            ItemInfo.BackgroundTransparency = 1
            ItemInfo.Font = Enum.Font.GothamBold
            ItemInfo.Text = string.format("🐾 %s  [%s]  ·  %s", tostring(item.animal), tostring(item.mutation or "Normal"), tostring(item.time or ""))
            ItemInfo.TextColor3 = Color3.fromRGB(240, 245, 255)
            ItemInfo.TextSize = 12
            ItemInfo.TextXAlignment = Enum.TextXAlignment.Left
            ItemInfo.Parent = Card

            local JoinBtn = Instance.new("TextButton")
            JoinBtn.Size = UDim2.new(0, 90, 0, 28)
            JoinBtn.Position = UDim2.new(1, -100, 0.5, -14)
            JoinBtn.BackgroundColor3 = Color3.fromRGB(245, 166, 35)
            JoinBtn.Font = Enum.Font.GothamBold
            JoinBtn.Text = "👤 Join"
            JoinBtn.TextColor3 = Color3.fromRGB(15, 17, 23)
            JoinBtn.TextSize = 11
            JoinBtn.Parent = Card

            local JoinCorner = Instance.new("UICorner")
            JoinCorner.CornerRadius = UDim.new(0, 6)
            JoinCorner.Parent = JoinBtn

            JoinBtn.MouseButton1Click:Connect(function()
                teleport_to_job(item.placeId, item.jobId, item.animal)
            end)
        end

        StealsPage.CanvasSize = UDim2.new(0, 0, 0, StealsLayout.AbsoluteContentSize.Y + 20)
    end

    -- Page 2: Brainrot Whitelist Filter
    local WhitelistPage = Instance.new("ScrollingFrame")
    WhitelistPage.Size = UDim2.new(1, -20, 1, -20)
    WhitelistPage.Position = UDim2.new(0, 10, 0, 10)
    WhitelistPage.BackgroundTransparency = 1
    WhitelistPage.BorderSizePixel = 0
    WhitelistPage.ScrollBarThickness = 4
    WhitelistPage.ScrollBarImageColor3 = Color3.fromRGB(245, 166, 35)
    WhitelistPage.Visible = false
    WhitelistPage.Parent = PageContainer

    local WGrid = Instance.new("UIGridLayout")
    WGrid.CellSize = UDim2.new(0, 200, 0, 34)
    WGrid.CellPadding = UDim2.new(0, 10, 0, 8)
    WGrid.Parent = WhitelistPage

    for brName, isEnabled in pairs(BRAINROT_WHITELIST) do
        local ItemBtn = Instance.new("TextButton")
        ItemBtn.Name = brName
        ItemBtn.BackgroundColor3 = isEnabled and Color3.fromRGB(35, 42, 60) or Color3.fromRGB(24, 28, 38)
        ItemBtn.Font = Enum.Font.GothamBold
        ItemBtn.Text = (isEnabled and "  [✓]  " or "  [  ]  ") .. brName
        ItemBtn.TextColor3 = isEnabled and Color3.fromRGB(255, 255, 255) or Color3.fromRGB(140, 150, 175)
        ItemBtn.TextSize = 12
        ItemBtn.TextXAlignment = Enum.TextXAlignment.Left
        ItemBtn.Parent = WhitelistPage

        local ItemCorner = Instance.new("UICorner")
        ItemCorner.CornerRadius = UDim.new(0, 8)
        ItemCorner.Parent = ItemBtn

        local ItemStroke = Instance.new("UIStroke")
        ItemStroke.Color = isEnabled and Color3.fromRGB(245, 166, 35) or Color3.fromRGB(40, 48, 65)
        ItemStroke.Thickness = 1
        ItemStroke.Parent = ItemBtn

        ItemBtn.MouseButton1Click:Connect(function()
            BRAINROT_WHITELIST[brName] = not BRAINROT_WHITELIST[brName]
            local active = BRAINROT_WHITELIST[brName]
            ItemBtn.BackgroundColor3 = active and Color3.fromRGB(35, 42, 60) or Color3.fromRGB(24, 28, 38)
            ItemBtn.Text = (active and "  [✓]  " or "  [  ]  ") .. brName
            ItemBtn.TextColor3 = active and Color3.fromRGB(255, 255, 255) or Color3.fromRGB(140, 150, 175)
            ItemStroke.Color = active and Color3.fromRGB(245, 166, 35) or Color3.fromRGB(40, 48, 65)
        end)
    end

    -- Page 3: Log Server Nodes
    local NodesPage = Instance.new("ScrollingFrame")
    NodesPage.Size = UDim2.new(1, -20, 1, -20)
    NodesPage.Position = UDim2.new(0, 10, 0, 10)
    NodesPage.BackgroundTransparency = 1
    NodesPage.BorderSizePixel = 0
    NodesPage.ScrollBarThickness = 4
    NodesPage.Visible = false
    NodesPage.Parent = PageContainer

    local NGrid = Instance.new("UIGridLayout")
    NGrid.CellSize = UDim2.new(0, 300, 0, 52)
    NGrid.CellPadding = UDim2.new(0, 12, 0, 10)
    NGrid.Parent = NodesPage

    local LogNodes = {
        { name = "Hanoi", sub = "Vietnam", flag = "🇻🇳", status = "RECOMMENDED", color = Color3.fromRGB(46, 204, 113) },
        { name = "Madrid", sub = "Spain · Live", flag = "🇪🇸", status = "ACTIVE", color = Color3.fromRGB(245, 166, 35) },
        { name = "Singapore", sub = "Singapore", flag = "🇸🇬", status = "ONLINE", color = Color3.fromRGB(52, 152, 219) },
        { name = "Tokyo", sub = "Japan", flag = "🇯🇵", status = "ONLINE", color = Color3.fromRGB(52, 152, 219) },
        { name = "Frankfurt", sub = "Germany", flag = "🇩🇪", status = "ONLINE", color = Color3.fromRGB(52, 152, 219) },
        { name = "Ashburn", sub = "Virginia, USA", flag = "🇺🇸", status = "ONLINE", color = Color3.fromRGB(52, 152, 219) },
        { name = "Dallas", sub = "Texas, USA", flag = "🇺🇸", status = "ONLINE", color = Color3.fromRGB(52, 152, 219) }
    }

    for _, n in ipairs(LogNodes) do
        local NodeBtn = Instance.new("TextButton")
        NodeBtn.BackgroundColor3 = Color3.fromRGB(26, 30, 42)
        NodeBtn.Text = ""
        NodeBtn.Parent = NodesPage

        local NCorner = Instance.new("UICorner")
        NCorner.CornerRadius = UDim.new(0, 10)
        NCorner.Parent = NodeBtn

        local NTitle = Instance.new("TextLabel")
        NTitle.Size = UDim2.new(1, -90, 0, 22)
        NTitle.Position = UDim2.new(0, 12, 0, 8)
        NTitle.BackgroundTransparency = 1
        NTitle.Font = Enum.Font.GothamBold
        NTitle.Text = n.flag .. " " .. n.name
        NTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
        NTitle.TextSize = 13
        NTitle.TextXAlignment = Enum.TextXAlignment.Left
        NTitle.Parent = NodeBtn

        local NSub = Instance.new("TextLabel")
        NSub.Size = UDim2.new(1, -90, 0, 16)
        NSub.Position = UDim2.new(0, 12, 0, 28)
        NSub.BackgroundTransparency = 1
        NSub.Font = Enum.Font.GothamMedium
        NSub.Text = n.sub
        NSub.TextColor3 = Color3.fromRGB(140, 150, 175)
        NSub.TextSize = 10
        NSub.TextXAlignment = Enum.TextXAlignment.Left
        NSub.Parent = NodeBtn

        local Tag = Instance.new("TextLabel")
        Tag.Size = UDim2.new(0, 80, 0, 22)
        Tag.Position = UDim2.new(1, -90, 0.5, -11)
        Tag.BackgroundColor3 = Color3.fromRGB(20, 24, 34)
        Tag.Font = Enum.Font.GothamBold
        Tag.Text = n.status
        Tag.TextColor3 = n.color
        Tag.TextSize = 9
        Tag.Parent = NodeBtn

        local TagCorner = Instance.new("UICorner")
        TagCorner.CornerRadius = UDim.new(0, 6)
        TagCorner.Parent = Tag

        NodeBtn.MouseButton1Click:Connect(function()
            CONFIG.SelectedNode = n.name .. " (" .. n.sub .. ")"
            RegionBtn.Text = n.flag .. " " .. string.sub(n.name, 1, 3):upper()
        end)
    end

    -- Tab Switching Logic
    local function switch_tab(tab_id)
        State.active_tab = tab_id
        StealsPage.Visible = (tab_id == "STEALS")
        WhitelistPage.Visible = (tab_id == "WHITELIST")
        NodesPage.Visible = (tab_id == "NODES")

        for _, btnData in ipairs(TabButtons) do
            local active = (btnData.id == tab_id)
            btnData.btn.BackgroundColor3 = active and Color3.fromRGB(20, 23, 32) or Color3.fromRGB(15, 17, 23)
            btnData.btn.TextColor3 = active and Color3.fromRGB(245, 166, 35) or Color3.fromRGB(140, 150, 175)
        end
    end

    for i, t in ipairs(Tabs) do
        local TabBtn = Instance.new("TextButton")
        TabBtn.Size = UDim2.new(0, 160, 1, 0)
        TabBtn.Position = UDim2.new(0, (i - 1) * 168, 0, 0)
        TabBtn.BackgroundColor3 = (t.id == "STEALS") and Color3.fromRGB(20, 23, 32) or Color3.fromRGB(15, 17, 23)
        TabBtn.Font = Enum.Font.GothamBold
        TabBtn.Text = t.label
        TabBtn.TextColor3 = (t.id == "STEALS") and Color3.fromRGB(245, 166, 35) or Color3.fromRGB(140, 150, 175)
        TabBtn.TextSize = 11
        TabBtn.Parent = TabContainer

        local TCorner = Instance.new("UICorner")
        TCorner.CornerRadius = UDim.new(0, 8)
        TCorner.Parent = TabBtn

        table.insert(TabButtons, { id = t.id, btn = TabBtn })

        TabBtn.MouseButton1Click:Connect(function()
            switch_tab(t.id)
        end)
    end

    -- Bottom Footer (Nigga Finder Style)
    local Footer = Instance.new("Frame")
    Footer.Size = UDim2.new(1, 0, 0, 35)
    Footer.Position = UDim2.new(0, 0, 1, -35)
    Footer.BackgroundColor3 = Color3.fromRGB(20, 23, 32)
    Footer.BorderSizePixel = 0
    Footer.Parent = MainFrame

    local FooterCorner = Instance.new("UICorner")
    FooterCorner.CornerRadius = UDim.new(0, 16)
    FooterCorner.Parent = Footer

    local FooterText = Instance.new("TextLabel")
    FooterText.Size = UDim2.new(1, -30, 1, 0)
    FooterText.Position = UDim2.new(0, 15, 0, 0)
    FooterText.BackgroundTransparency = 1
    FooterText.Font = Enum.Font.GothamBold
    FooterText.Text = "⚡ NIGGA FINDER v2  ·  discord.gg/niggafinder"
    FooterText.TextColor3 = Color3.fromRGB(245, 166, 35)
    FooterText.TextSize = 11
    FooterText.TextXAlignment = Enum.TextXAlignment.Center
    FooterText.Parent = Footer

    -- Keybind Listener [T]
    UserInputService.InputBegan:Connect(function(input, gpe)
        if not gpe and input.KeyCode == Enum.KeyCode.T then
            State.gui_visible = not State.gui_visible
            MainFrame.Visible = State.gui_visible
        end
    end)

    UI.RefreshStealsList()
end

-- ── STARTUP ────────────────────────────────────────────────────
task.spawn(create_ui)
task.spawn(start_websocket)
task.spawn(start_steal_watch)
