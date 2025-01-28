import { useToast as useToastHook } from "@/hooks/use-toast"

export { type ToastActionElement, type ToastProps } from "@/components/ui/toast"

export function useToast() {
  return useToastHook()
}
