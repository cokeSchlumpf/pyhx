"""Current-user accessors backed by :class:`RequestContext`."""

from commons.users import AnonymousUser, AuthenticatedUser, RegisteredUser, User

from pyhx.core import RequestContext

from ._exception import NotAuthenticated


def require_user() -> User:
    """Return the current request's :class:`User` from the active
    :class:`RequestContext`.

    Within a request, the user is always populated — by
    :class:`CookieUserSession` from the session cookie, or as an
    :class:`AnonymousUser` when there is no signed-in viewer. This
    function does **not** gate on identity (anonymous viewers are
    returned as-is); use :func:`require_authenticated_user` or
    :func:`require_registered_user` for that.

    Outside a request (background tasks, scripts, code paths not
    driven by the framework's request handling) there is no
    :class:`RequestContext` set and :meth:`RequestContext.get` raises
    :class:`LookupError`. Callers in those contexts should either set
    a context themselves via
    :func:`pyhx.core.request_context.set_request_context` or avoid
    this helper.
    """
    return RequestContext.get().user


def require_authenticated_user() -> AuthenticatedUser | RegisteredUser:
    """Return the current user when it represents a real identity
    (either an :class:`AuthenticatedUser` from an external system or a
    locally :class:`RegisteredUser`); raise :class:`NotAuthenticated`
    otherwise.

    Use from handlers / dependencies that need a signed-in user but
    don't care whether they have a local account row. The raise gets
    converted into a redirect to ``login_path`` by the addon's
    exception handler (see :func:`configure_user_authentication`).

    Delegates the context lookup to :func:`require_user`, so any
    :class:`LookupError` raised when there is no active
    :class:`RequestContext` propagates unchanged.
    """
    user = require_user()
    if isinstance(user, AnonymousUser):
        raise NotAuthenticated()

    assert isinstance(user, (AuthenticatedUser, RegisteredUser))
    return user


def require_registered_user() -> RegisteredUser:
    """Return the current user when it's a :class:`RegisteredUser`
    (i.e. backed by a local account row); raise
    :class:`NotAuthenticated` otherwise — including for externally
    authenticated users without a local account.

    Stricter than :func:`require_authenticated_user`. Note that for
    an :class:`AuthenticatedUser` the redirect-to-login UX is
    technically wrong (they're already signed in); a future
    ``RegistrationRequired`` exception with its own handler can refine
    this, but until then ``NotAuthenticated`` is the closest fit.

    Delegates the context lookup to :func:`require_user`, so any
    :class:`LookupError` raised when there is no active
    :class:`RequestContext` propagates unchanged.
    """
    user = require_user()
    if not isinstance(user, RegisteredUser):
        raise NotAuthenticated()
    return user
