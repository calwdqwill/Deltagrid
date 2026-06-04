import {
  ArbitrageScannerData,
  AssetDeepDiveData,
  FundingData,
  MarketMatrixData,
  MarketOverviewData,
  PerpDexData,
  StrategyLabData,
} from "@/types/terminal";
import {
  arbitrageScannerFixture,
  assetDeepDiveFixture,
  fundingFixture,
  marketMatrixFixture,
  marketOverviewFixture,
  perpDexFixture,
  strategyLabFixture,
} from "./fixtures";

export interface TerminalDataAdapter {
  getMarketOverview(): Promise<MarketOverviewData>;
  getPerpDexOverview(): Promise<PerpDexData>;
  getFundingOverview(): Promise<FundingData>;
  getAssetDeepDive(symbol: string): Promise<AssetDeepDiveData>;
  getMarketMatrix(): Promise<MarketMatrixData>;
  getStrategyLab(): Promise<StrategyLabData>;
  getArbitrageScanner(): Promise<ArbitrageScannerData>;
}

class MockTerminalDataAdapter implements TerminalDataAdapter {
  async getMarketOverview() {
    return marketOverviewFixture;
  }

  async getPerpDexOverview() {
    return perpDexFixture;
  }

  async getFundingOverview() {
    return fundingFixture;
  }

  async getAssetDeepDive(_symbol: string) {
    return assetDeepDiveFixture;
  }

  async getMarketMatrix() {
    return marketMatrixFixture;
  }

  async getStrategyLab() {
    return strategyLabFixture;
  }

  async getArbitrageScanner() {
    return arbitrageScannerFixture;
  }
}

export const terminalDataAdapter: TerminalDataAdapter = new MockTerminalDataAdapter();
