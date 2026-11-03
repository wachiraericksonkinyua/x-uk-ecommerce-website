import type { Directive } from "vue";

type Handler = {
  move: (event: MouseEvent) => void;
  leave: () => void;
};

const handlers = new WeakMap<HTMLElement, Handler>();

/**
 * Subtle magnetic displacement for pointer devices only.
 *
 * The element follows the cursor by a fraction of the distance from its centre,
 * then springs back when the pointer leaves. Touch devices are untouched.
 */
export const magnetic: Directive<HTMLElement> = {
  mounted(el) {
    if (!window.matchMedia("(pointer: fine)").matches) return;

    el.style.willChange = "transform";
    el.style.transition = "transform 180ms cubic-bezier(0.22, 1, 0.36, 1)";

    const move = (event: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      const offsetX = event.clientX - (rect.left + rect.width / 2);
      const offsetY = event.clientY - (rect.top + rect.height / 2);
      const x = Math.max(-10, Math.min(10, offsetX * 0.14));
      const y = Math.max(-8, Math.min(8, offsetY * 0.18));
      el.style.transform = `translate(${x}px, ${y}px)`;
    };

    const leave = () => {
      el.style.transform = "";
    };

    el.addEventListener("mousemove", move);
    el.addEventListener("mouseleave", leave);
    handlers.set(el, { move, leave });
  },
  unmounted(el) {
    const handler = handlers.get(el);
    if (!handler) return;
    el.removeEventListener("mousemove", handler.move);
    el.removeEventListener("mouseleave", handler.leave);
    handlers.delete(el);
  },
};
