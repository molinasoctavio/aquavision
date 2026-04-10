"use client";
import { useEffect, useRef } from "react";

interface Props {
  src: string;
  hlsPath?: string;
  onTimeUpdate?: (ms: number) => void;
  onPlayPause?: (playing: boolean) => void;
  playerRef?: React.MutableRefObject<any>;
}

export default function VideoPlayer({ src, hlsPath, onTimeUpdate, onPlayPause, playerRef }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const vjsRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !videoRef.current) return;

    let player: any;
    import("video.js").then(({ default: videojs }) => {
      const streamSrc = hlsPath
        ? { src: hlsPath, type: "application/x-mpegURL" }
        : { src, type: "video/mp4" };

      player = videojs(videoRef.current!, {
        autoplay: false,
        controls: true,
        fluid: true,
        responsive: true,
        playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2],
        sources: [streamSrc],
        html5: {
          hls: { overrideNative: true },
        },
      });

      player.addClass("vjs-aquavision");

      player.on("timeupdate", () => {
        onTimeUpdate?.(Math.floor(player.currentTime() * 1000));
      });
      player.on("play", () => onPlayPause?.(true));
      player.on("pause", () => onPlayPause?.(false));

      vjsRef.current = player;
      if (playerRef) playerRef.current = player;
    });

    return () => {
      if (player && !player.isDisposed()) player.dispose();
    };
  }, [src, hlsPath]);

  return (
    <div className="w-full h-full flex items-center justify-center bg-black">
      <div data-vjs-player className="w-full max-h-full">
        <video ref={videoRef} className="video-js vjs-default-skin vjs-big-play-centered w-full" />
      </div>
    </div>
  );
}
