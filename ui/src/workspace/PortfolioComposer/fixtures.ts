import type { PortfolioMember } from '../../app/types';
import { strategies } from '../../plugins/databank/fixtures';

export const portfolioMembers: PortfolioMember[] = strategies.slice(58, 66).map((s, i) => ({ strategyId: s.id, weight: i < 4 ? 15 : 10, enabled: true, sector: i % 3 === 0 ? 'FX Majors' : i % 3 === 1 ? 'Metals' : 'Indices' }));
