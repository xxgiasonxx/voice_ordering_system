import { createBrowserRouter } from "react-router-dom";
import ErrorPage from "../pages/Error";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <p> Welcome to the Home Page</p>,
    errorElement: <ErrorPage />,
  },
  {
    path: "/products",
    element: <p> Welcome to the Products Page</p>,
  },
  {
    path: "/user",
    element: <p> Welcome to the User Page</p>,
  },
]);