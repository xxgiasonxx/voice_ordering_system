import { createBrowserRouter } from "react-router-dom";
import ErrorPage from "../pages/Error";
import Homepage from "../pages/Home";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Homepage />,
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