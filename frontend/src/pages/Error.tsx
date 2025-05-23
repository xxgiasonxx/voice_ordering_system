import { Link, Outlet } from "react-router-dom";

export default function ErrorPage() {
  return (
    <>
      <div>
          <p>The path is no exist</p>
          <p>back to home</p>
          <Link to="/">Go Home</Link>
      </div>
      <Outlet />
    </>
  );
}