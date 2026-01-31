"use client";

import { useState, useMemo } from "react";
import { Bot } from "lucide-react";
import type { Agent, AgentEvent, GuardrailCheck } from "@/lib/types";
import { AgentsList } from "./agents-list";
import { Guardrails } from "./guardrails";
import { ConversationContext } from "./conversation-context";
import { RunnerOutput } from "./runner-output";
import { SeatMap } from "./seat-map";

interface AgentPanelProps {
  agents: Agent[];
  currentAgent: string;
  events: AgentEvent[];
  guardrails: GuardrailCheck[];
  context: Record<string, any>;
}

export function AgentPanel({
  agents,
  currentAgent,
  events,
  guardrails,
  context,
}: AgentPanelProps) {
  const [selectedSeat, setSelectedSeat] = useState<string | undefined>(undefined);
  
  const activeAgent = agents.find((a) => a.name === currentAgent);
  const runnerEvents = events.filter(
    (e) => e.type !== "message" && e.type !== "progress_update"
  );

  // Check if seat map should be shown based on tool output
  const showSeatMap = useMemo(() => {
    return events.some(
      (e) => e.type === "tool_output" && e.content?.includes("DISPLAY_SEAT_MAP")
    );
  }, [events]);

  const handleSeatSelect = (seatNumber: string) => {
    setSelectedSeat(seatNumber);
    // The seat selection could be used to send a message back to the agent
    console.log(`Selected seat: ${seatNumber}`);
  };

  return (
    <div className="w-3/5 h-full flex flex-col border-r border-gray-200 bg-white rounded-xl shadow-sm">
      <div className="bg-blue-600 text-white h-12 px-4 flex items-center gap-3 shadow-sm rounded-t-xl">
        <Bot className="h-5 w-5" />
        <h1 className="font-semibold text-sm sm:text-base lg:text-lg">
          Agent View
        </h1>
        <span className="ml-auto text-xs font-light tracking-wide opacity-80">
          Airline&nbsp;Co.
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50">
        <AgentsList agents={agents} currentAgent={currentAgent} />
        <ConversationContext context={context} />
        <Guardrails
          guardrails={guardrails}
          inputGuardrails={activeAgent?.input_guardrails ?? []}
        />
        <RunnerOutput runnerEvents={runnerEvents} />
        {showSeatMap && (
          <div className="mt-4">
            <SeatMap onSeatSelect={handleSeatSelect} selectedSeat={selectedSeat} />
          </div>
        )}
      </div>
    </div>
  );
}
