import * as React from "react"

import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, value, ...props }, ref) => {
  // Campi numerici: lo zero di default si mostra vuoto, così si digita subito senza cancellare "0"
  const shown = type === "number" && (value === 0 || value === "0") && !props.readOnly ? "" : value;
  const onFocus = (e) => {
    if (type === "number" && e.target.value === "0") e.target.select();
    props.onFocus?.(e);
  };
  return (
    <input
      type={type}
      value={shown}
      onFocus={onFocus}
      className={cn(
        "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Input.displayName = "Input"

export { Input }
