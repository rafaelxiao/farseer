import { useState, useEffect, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"

interface PlaybackControlsProps {
  totalBars: number
  currentBar: number
  onBarChange: (bar: number) => void
  isPlaying: boolean
  onPlayPause: () => void
  speed: number
  onSpeedChange: (speed: number) => void
  onReset: () => void
  startDate?: string
  endDate?: string
  currentDate?: string
}

const SPEEDS = [0.5, 1, 2, 5, 10, 20]

export default function PlaybackControls({
  totalBars,
  currentBar,
  onBarChange,
  isPlaying,
  onPlayPause,
  speed,
  onSpeedChange,
  onReset,
  startDate,
  endDate,
  currentDate,
}: PlaybackControlsProps) {
  const progress = totalBars > 0 ? (currentBar / totalBars) * 100 : 0

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onBarChange(parseInt(e.target.value))
  }

  const handleStepBack = () => {
    onBarChange(Math.max(0, currentBar - 1))
  }

  const handleStepForward = () => {
    onBarChange(Math.min(totalBars - 1, currentBar + 1))
  }

  const handleJumpBack = () => {
    onBarChange(Math.max(0, currentBar - 10))
  }

  const handleJumpForward = () => {
    onBarChange(Math.min(totalBars - 1, currentBar + 10))
  }

  const cycleSpeed = () => {
    const currentIndex = SPEEDS.indexOf(speed)
    const nextIndex = (currentIndex + 1) % SPEEDS.length
    onSpeedChange(SPEEDS[nextIndex])
  }

  return (
    <div className="space-y-3">
      {/* Progress bar */}
      <div className="relative">
        <input
          type="range"
          min={0}
          max={totalBars - 1}
          value={currentBar}
          onChange={handleSliderChange}
          className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, hsl(var(--primary)) ${progress}%, hsl(var(--secondary)) ${progress}%)`,
          }}
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>{startDate || "Start"}</span>
          <span className="font-medium text-foreground">
            {currentDate || `Bar ${currentBar + 1} / ${totalBars}`}
          </span>
          <span>{endDate || "End"}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-2">
        {/* Reset */}
        <Button
          variant="outline"
          size="sm"
          onClick={onReset}
          title="Reset to start"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="19 20 9 12 19 4 19 20" />
            <line x1="5" y1="19" x2="5" y2="5" />
          </svg>
        </Button>

        {/* Jump back 10 */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleJumpBack}
          title="Back 10 bars"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="11 19 2 12 11 5 11 19" />
            <polygon points="22 19 13 12 22 5 22 19" />
          </svg>
        </Button>

        {/* Step back */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleStepBack}
          title="Previous bar"
          disabled={currentBar <= 0}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="19 20 9 12 19 4 19 20" />
          </svg>
        </Button>

        {/* Play/Pause */}
        <Button
          variant={isPlaying ? "default" : "outline"}
          size="sm"
          onClick={onPlayPause}
          className="w-10 h-10"
          title={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          )}
        </Button>

        {/* Step forward */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleStepForward}
          title="Next bar"
          disabled={currentBar >= totalBars - 1}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="5 4 15 12 5 20 5 4" />
          </svg>
        </Button>

        {/* Jump forward 10 */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleJumpForward}
          title="Forward 10 bars"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="13 19 22 12 13 5 13 19" />
            <polygon points="2 19 11 12 2 5 2 19" />
          </svg>
        </Button>

        {/* Speed */}
        <Button
          variant="outline"
          size="sm"
          onClick={cycleSpeed}
          title="Change speed"
          className="min-w-[50px]"
        >
          {speed}x
        </Button>
      </div>

      {/* Keyboard shortcuts hint */}
      <div className="text-center text-xs text-muted-foreground">
        <span className="mr-3">Space: Play/Pause</span>
        <span className="mr-3">←→: Step</span>
        <span className="mr-3">⇧←⇧→: Jump 10</span>
        <span>R: Reset</span>
      </div>
    </div>
  )
}
