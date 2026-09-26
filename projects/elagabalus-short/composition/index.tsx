import React from "react";
import { Composition, registerRoot } from "remotion";
import { DURATION_S, FPS, H, Short, W } from "./Short";

const Root: React.FC = () => (
  <Composition
    id="ElagabalusShort"
    component={Short}
    width={W}
    height={H}
    fps={FPS}
    durationInFrames={Math.round(DURATION_S * FPS)}
  />
);

registerRoot(Root);
