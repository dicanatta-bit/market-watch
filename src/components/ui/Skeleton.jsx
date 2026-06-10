import { forwardRef } from 'react'
import { cn } from '../../lib/utils.js'

const Skeleton = forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('animate-pulse rounded-md bg-muted', className)} {...props} />
))
Skeleton.displayName = 'Skeleton'
export { Skeleton }
