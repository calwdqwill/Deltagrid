export interface Dictionary {
  app: {
    name: string;
    tagline: string;
  };
  nav: {
    scanner: string;
    settings: string;
    paperTrading: string;
    profile: string;
    market: string;
    execution: string;
    exchangeAccounts: string;
    riskRules: string;
    alerts: string;
    notifications: string;
    login: string;
    logout: string;
    rwa: string;
    treasury: string;
  };
  scanner: {
    title: string;
    searchPlaceholder: string;
    minSpread: string;
    minVolume: string;
    positiveNetOnly: string;
    refresh: string;
    refreshing: string;
    lastUpdated: string;
    nextUpdate: string;
    columns: {
      token: string;
      type: string;
      buyAt: string;
      buyPrice: string;
      sellAt: string;
      sellPrice: string;
      spread: string;
      netProfit: string;
      volume24h: string;
      signal: string;
      trend: string;
      actions: string;
    };
    tabs: {
      all: string;
      cexCex: string;
      dexCex: string;
      spotPerp: string;
      favorites: string;
      pinned: string;
    };
    empty: string;
    loading: string;
    error: string;
    stale: string;
    fallback: string;
  };
  detail: {
    title: string;
    back: string;
    buyCard: string;
    sellCard: string;
    spread: string;
    netProfit: string;
    signal: string;
    calculation: string;
    basis: string;
    fundingRate: string;
    openInterest: string;
    unavailable: string;
  };
  settings: {
    title: string;
    language: string;
    scannerPrefs: string;
    thresholds: string;
    minSpread: string;
    refreshInterval: string;
    slippage: string;
    feeBuy: string;
    feeSell: string;
    dataSources: string;
    save: string;
    saved: string;
  };
  signals: {
    STRONG: string;
    BUY_SELL: string;
    MARGINAL: string;
    HOLD: string;
  };
  status: {
    live: string;
    cached: string;
    stale: string;
    fallback: string;
    partial: string;
    unavailable: string;
  };
  kpi: {
    opportunities: string;
    bestSpread: string;
    avgSpread: string;
    activeSignals: string;
  };
  auth: {
    loginTitle: string;
    registerTitle: string;
    email: string;
    password: string;
    username: string;
    loginButton: string;
    registerButton: string;
    noAccount: string;
    hasAccount: string;
    logoutConfirm: string;
  };
  paper: {
    title: string;
    balance: string;
    initialBalance: string;
    pnl: string;
    winRate: string;
    trades: string;
    openTrades: string;
    closedTrades: string;
    strategy: string;
    entryPrice: string;
    exitPrice: string;
    quantity: string;
    closeTrade: string;
  };
  market: {
    title: string;
    trending: string;
    topGainers: string;
    topLosers: string;
    globalStats: string;
    marketCap: string;
    volume24h: string;
    btcDominance: string;
    ethDominance: string;
    activeCryptos: string;
    price: string;
    change24h: string;
    rank: string;
    fearGreed: string;
    fearGreedHistory: string;
    extremeFear: string;
    neutral: string;
    extremeGreed: string;
    newListings: string;
    fundingRates: string;
  };
  exchangeAccounts: {
    title: string;
    addAccount: string;
    connected: string;
    notConnected: string;
    apiKey: string;
    apiSecret: string;
    passphrase: string;
    testnet: string;
    deleteConfirm: string;
    exchange: string;
    label: string;
    type: string;
    status: string;
    noAccounts: string;
  };
  execution: {
    title: string;
    orders: string;
    intents: string;
    newIntent: string;
    confirmIntent: string;
    dryRun: string;
    liveTrading: string;
    orderStatus: {
      intent: string;
      riskChecked: string;
      pendingConfirmation: string;
      submitted: string;
      filled: string;
      partiallyFilled: string;
      cancelled: string;
      rejected: string;
      failed: string;
    };
  };
  risk: {
    title: string;
    rules: string;
    addRule: string;
    killSwitch: string;
    maxPositionSize: string;
    maxExposure: string;
    maxDailyLoss: string;
    actionBlock: string;
    actionWarn: string;
    noRules: string;
  };
  rwa: {
    title: string;
    categories: {
      tokenizedGold: string;
      tokenizedTreasury: string;
      tokenizedCredit: string;
      other: string;
    };
    columns: {
      symbol: string;
      name: string;
      category: string;
      issuer: string;
      price: string;
      nav: string;
      premiumDiscount: string;
      source: string;
      freshness: string;
    };
    empty: string;
    loading: string;
  };
  treasury: {
    title: string;
    btcHoldings: string;
    companies: string;
    platforms: string;
    empty: string;
    loading: string;
  };
}
