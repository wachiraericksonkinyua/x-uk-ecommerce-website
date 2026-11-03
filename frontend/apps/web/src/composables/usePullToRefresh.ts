import { computed, onBeforeUnmount, onMounted, ref } from "vue";

interface PullToRefreshOptions {
  threshold?: number;
  maxPull?: number;
}

/**
 * Mobile pull-to-refresh gesture for scrollable pages.
 *
 * The gesture only activates on small screens when the page is already at the
 * top, so normal scrolling is unaffected lower down the page.
 */
export function usePullToRefresh(
  onRefresh: () => Promise<unknown> | unknown,
  options: PullToRefreshOptions = {}
) {
  const threshold = options.threshold ?? 70;
  const maxPull = options.maxPull ?? 110;

  const pullDistance = ref(0);
  const refreshing = ref(false);
  const ready = computed(() => pullDistance.value >= threshold);

  let startY = 0;
  let tracking = false;

  function isMobileViewport() {
    return window.matchMedia("(max-width: 1023px)").matches;
  }

  function onTouchStart(event: TouchEvent) {
    if (!isMobileViewport() || refreshing.value) return;
    if (window.scrollY > 0 || event.touches.length !== 1) return;
    startY = event.touches[0].clientY;
    tracking = true;
  }

  function onTouchMove(event: TouchEvent) {
    if (!tracking || event.touches.length !== 1) return;

    const delta = event.touches[0].clientY - startY;
    if (delta <= 0 || window.scrollY > 0) {
      pullDistance.value = 0;
      tracking = false;
      return;
    }

    // Add resistance so the sheet feels physical rather than 1:1.
    pullDistance.value = Math.min(maxPull, delta * 0.55);
    if (pullDistance.value > 4) event.preventDefault();
  }

  async function onTouchEnd() {
    if (!tracking) return;
    tracking = false;

    if (pullDistance.value < threshold) {
      pullDistance.value = 0;
      return;
    }

    refreshing.value = true;
    pullDistance.value = threshold;
    try {
      await onRefresh();
    } finally {
      refreshing.value = false;
      pullDistance.value = 0;
    }
  }

  onMounted(() => {
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: false });
    window.addEventListener("touchend", onTouchEnd);
    window.addEventListener("touchcancel", onTouchEnd);
  });

  onBeforeUnmount(() => {
    window.removeEventListener("touchstart", onTouchStart);
    window.removeEventListener("touchmove", onTouchMove);
    window.removeEventListener("touchend", onTouchEnd);
    window.removeEventListener("touchcancel", onTouchEnd);
  });

  return { pullDistance, refreshing, ready };
}
