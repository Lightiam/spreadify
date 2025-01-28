import { useToast as useToastHook } from "@/components/ui/toast"

export { type ToastActionElement, type ToastProps } from "@/components/ui/toast"

export function useToast() {
  return useToastHook()
}
