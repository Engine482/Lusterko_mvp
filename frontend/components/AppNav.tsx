"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { authApi, type AuthMe } from "@/lib/api/auth";
import { humanError } from "@/lib/api/messages";
import { ROLE_LABEL } from "@/lib/labels";
import type { Role } from "@/types/enums";

const HOME_PATH: Record<Role, string> = {
  soldier: "/soldier",
  commander: "/commander",
  medic_psych: "/medic",
  admin: "/admin",
};

export function getHomeRouteForRole(role: Role | null): string {
  return role ? HOME_PATH[role] : "/";
}

export function AppNav() {
  const [me, setMe] = useState<AuthMe | null>(null);
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    authApi
      .me()
      .then((res) => {
        if (!cancelled) setMe(res);
      })
      .catch(() => {
        if (!cancelled) setMe(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!me) return null;

  const home = getHomeRouteForRole(me.active_role);
  const multiRole = me.roles.length > 1;
  const activeRoleLabel = me.active_role ? ROLE_LABEL[me.active_role] : "—";

  const close = () => setOpen(false);

  const logout = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await authApi.logout();
    } catch (err) {
      setError(humanError(err));
      setSubmitting(false);
      return;
    }
    window.location.assign("/login");
  };

  return (
    <div className="app-nav">
      <span
        className="app-nav__role-badge"
        aria-label={`Активна роль: ${activeRoleLabel}`}
      >
        Роль: {activeRoleLabel}
      </span>
      <button
        ref={buttonRef}
        type="button"
        className="app-nav__burger"
        aria-label={open ? "Закрити меню" : "Відкрити меню"}
        aria-expanded={open}
        aria-controls="app-nav-menu"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="app-nav__burger-icon" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </button>
      {open && (
        <>
          <div
            className="app-nav__backdrop"
            aria-hidden="true"
            onClick={close}
          />
          <div
            ref={menuRef}
            id="app-nav-menu"
            className="app-nav__menu"
            role="menu"
            aria-label="Меню навігації"
          >
            <button
              type="button"
              className="app-nav__close"
              onClick={close}
              aria-label="Закрити меню"
            >
              ✕
            </button>
            <Link
              className="app-nav__item"
              role="menuitem"
              href={home}
              onClick={close}
            >
              Головна
            </Link>
            <Link
              className="app-nav__item"
              role="menuitem"
              href="/settings/profile"
              onClick={close}
            >
              Налаштування
            </Link>
            {multiRole && (
              <Link
                className="app-nav__item"
                role="menuitem"
                href="/role"
                onClick={close}
              >
                Змінити роль
              </Link>
            )}
            <button
              type="button"
              role="menuitem"
              className="app-nav__item app-nav__item--danger"
              onClick={logout}
              disabled={submitting}
            >
              {submitting ? "Вихід…" : "Вийти"}
            </button>
            {error && (
              <span className="app-nav__error" role="alert">
                {error}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}
