import { redirect } from "next/navigation";

/**
 * Home Page
 *
 * Redirects to the projects page.
 */
export default function Home() {
  redirect("/projects");
}
