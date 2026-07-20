"use client"

import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ShieldBan, Zap } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { PendingOrderType } from "@/types/live"
import type { AccountMode } from "@/types/agentic-core"
import { useSettings } from "@/lib/use-settings"
import { defaultTradingPreferences } from "@/lib/trading-defaults"

interface ManualOrderControlsProps {
  sessionId?: number
  defaultSymbol?: string
}

export function ManualOrderControls({ sessionId, defaultSymbol }: ManualOrderControlsProps) {
  const { toast } = useToast()
  const { getJSONField, settings } = useSettings()

  const [volume, setVolume] = useState<string>("0.1")
  const [slPips, setSlPips] = useState<string>("")
  const [tpPips, setTpPips] = useState<string>("")
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [pendingType, setPendingType] = useState<PendingOrderType>("buy_limit")
  const [pendingPrice, setPendingPrice] = useState<string>("")
  const accountMode: AccountMode = "disabled"
  const killSwitchStatus = "unknown"
  const riskGovernorStatus = "approval token required"

  const requestGovernedExecution = (action: string) => {
    toast({
      title: "Governed workflow required",
      description: `${action} must be requested through the CEO workflow with evidence, RiskGovernor approval, and an approval token before Order Router execution.`,
    })
  }

  const availableSymbols = useMemo(() => {
    let forex = defaultTradingPreferences.forexSymbols.split(",")
    let commodities = defaultTradingPreferences.commoditySymbols.split(",")
    let indices = defaultTradingPreferences.indicesSymbols.split(",")

    if (settings) {
      const prefs = getJSONField("trading_preferences")
      if (prefs) {
        // If user has saved preferences, override defaults where present
        if (prefs.forexSymbols !== undefined) {
            forex = prefs.forexSymbols ? prefs.forexSymbols.split(",") : []
        }
        if (prefs.commoditySymbols !== undefined) {
             commodities = prefs.commoditySymbols ? prefs.commoditySymbols.split(",") : []
        }
        if (prefs.indicesSymbols !== undefined) {
             indices = prefs.indicesSymbols ? prefs.indicesSymbols.split(",") : []
        }
      }
    }

    // Clean and merge
    const cleanList = (list: string[]) => list.map(s => s.trim()).filter(s => s.length > 0)

    const allSymbols = Array.from(new Set([
        ...cleanList(forex),
        ...cleanList(commodities),
        ...cleanList(indices)
    ])).sort()

    return allSymbols.length > 0 ? allSymbols : ["XAUUSD"]
  }, [settings, getJSONField])

  const symbol =
    selectedSymbol && availableSymbols.includes(selectedSymbol)
      ? selectedSymbol
      : defaultSymbol && availableSymbols.includes(defaultSymbol)
        ? defaultSymbol
        : availableSymbols.includes("XAUUSD")
          ? "XAUUSD"
          : availableSymbols[0]

  const handleOrder = (type: "buy" | "sell") => {
    if (!sessionId) {
      toast({
        title: "No Session",
        description: "Please start a trading session first.",
        variant: "destructive",
      })
      return
    }

    if (!volume || Number.parseFloat(volume) <= 0) {
      toast({
        title: "Invalid Volume",
        description: "Please enter a valid volume.",
        variant: "destructive",
      })
      return
    }

    requestGovernedExecution(`${type.toUpperCase()} ${symbol}`)
  }

  const handleFlattenAll = () => {
    if (!sessionId) {
      toast({
        title: "No Session",
        description: "Please start a trading session first.",
        variant: "destructive",
      })
      return
    }

    requestGovernedExecution("Flatten all positions")
  }

  const handlePanicStop = () => {
    if (!sessionId) {
      toast({
        title: "No Session",
        description: "Please start a trading session first.",
        variant: "destructive",
      })
      return
    }

    requestGovernedExecution("Panic close and stop")
  }

  const handlePendingOrder = () => {
    if (!sessionId) {
      toast({
        title: "No Session",
        description: "Please start a trading session first.",
        variant: "destructive",
      })
      return
    }

    if (!volume || Number.parseFloat(volume) <= 0) {
      toast({
        title: "Invalid Volume",
        description: "Please enter a valid volume.",
        variant: "destructive",
      })
      return
    }

    if (!pendingPrice || Number.parseFloat(pendingPrice) <= 0) {
      toast({
        title: "Invalid Price",
        description: "Please enter a valid pending price.",
        variant: "destructive",
      })
      return
    }

    requestGovernedExecution(`${pendingType.replace("_", " ").toUpperCase()} ${symbol}`)
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Quick Execution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs">
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">Account mode: {accountMode}</Badge>
            <Badge variant="outline">Kill switch: {killSwitchStatus}</Badge>
            <Badge variant="outline">RiskGovernor: {riskGovernorStatus}</Badge>
          </div>
          <p className="mt-2 text-muted-foreground">
            These controls create governed CEO workflow requests only. Orders still require evidence, approval, RiskGovernor token validation, and Order Router execution.
          </p>
        </div>
        <Tabs defaultValue="market" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="market">Market</TabsTrigger>
                <TabsTrigger value="pending">Pending</TabsTrigger>
            </TabsList>
            <TabsContent value="market" className="space-y-4 pt-4">
                <div className="space-y-2">
                    <Label className="text-xs text-muted-foreground">Symbol</Label>
                    <Select value={symbol} onValueChange={setSelectedSymbol}>
                        <SelectTrigger>
                            <SelectValue placeholder="Select symbol" />
                        </SelectTrigger>
                        <SelectContent>
                            {availableSymbols.map((sym: string) => (
                                <SelectItem key={sym} value={sym}>
                                    {sym}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-2">
                    <Label className="text-xs text-muted-foreground">Volume (Lots)</Label>
                    <div className="flex items-center space-x-2">
                        <Input
                            type="number"
                            step="0.01"
                            value={volume}
                            onChange={(e) => setVolume(e.target.value)}
                            className="w-full"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">SL (Pips)</Label>
                        <Input
                            type="number"
                            placeholder="Optional"
                            value={slPips}
                            onChange={(e) => setSlPips(e.target.value)}
                        />
                    </div>
                    <div className="space-y-1">
                        <Label className="text-xs text-muted-foreground">TP (Pips)</Label>
                        <Input
                            type="number"
                            placeholder="Optional"
                            value={tpPips}
                            onChange={(e) => setTpPips(e.target.value)}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2">
                    <Button
                        variant="outline"
                        className="text-red-500 hover:text-red-600 border-red-200 hover:bg-red-50 dark:border-red-900/30 dark:hover:bg-red-900/20"
                        onClick={() => handleOrder("sell")}
                    >
                        Request SELL
                    </Button>
                    <Button
                        variant="outline"
                        className="text-emerald-500 hover:text-emerald-600 border-emerald-200 hover:bg-emerald-50 dark:border-emerald-900/30 dark:hover:bg-emerald-900/20"
                        onClick={() => handleOrder("buy")}
                    >
                        Request BUY
                    </Button>
                </div>
            </TabsContent>
            <TabsContent value="pending" className="pt-4">
                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label className="text-xs text-muted-foreground">Order Type</Label>
                        <Select
                          value={pendingType}
                          onValueChange={(value: PendingOrderType) => setPendingType(value)}
                        >
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="buy_limit">Buy Limit</SelectItem>
                                <SelectItem value="sell_limit">Sell Limit</SelectItem>
                                <SelectItem value="buy_stop">Buy Stop</SelectItem>
                                <SelectItem value="sell_stop">Sell Stop</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label className="text-xs text-muted-foreground">Price</Label>
                        <Input
                          type="number"
                          placeholder="Pending price"
                          value={pendingPrice}
                          onChange={(e) => setPendingPrice(e.target.value)}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                        <div className="space-y-1">
                            <Label className="text-xs text-muted-foreground">SL (Pips)</Label>
                            <Input
                                type="number"
                                placeholder="Optional"
                                value={slPips}
                                onChange={(e) => setSlPips(e.target.value)}
                            />
                        </div>
                        <div className="space-y-1">
                            <Label className="text-xs text-muted-foreground">TP (Pips)</Label>
                            <Input
                                type="number"
                                placeholder="Optional"
                                value={tpPips}
                                onChange={(e) => setTpPips(e.target.value)}
                            />
                        </div>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handlePendingOrder}
                    >
                        Request Pending Order
                    </Button>
                </div>
            </TabsContent>
        </Tabs>

        <div className="pt-4 border-t space-y-2">
             <Button
               variant="secondary"
               className="w-full text-xs h-8"
               onClick={handleFlattenAll}
             >
                <Zap className="mr-2 h-3 w-3" /> Request Flatten All
             </Button>
             <Button
               variant="destructive"
               className="w-full text-xs h-8"
               onClick={handlePanicStop}
             >
                <ShieldBan className="mr-2 h-3 w-3" /> Request Panic Stop
             </Button>
        </div>
      </CardContent>
    </Card>
  )
}
