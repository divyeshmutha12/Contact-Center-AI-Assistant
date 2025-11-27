import Image from "next/image";

export function LangGraphLogoSVG({
  className,
  width = 60,
  height = 60,
}: {
  width?: number;
  height?: number;
  className?: string;
}) {
  return (
    <Image
      src="/azalio_logo.png"
      alt="Azalio Logo"
      width={width}
      height={height}
      className={`object-contain ${className || ""}`}
      priority
    />
  );
}
