from django.conf import settings
from django.utils.translation import ugettext as _

from tastypie.exceptions import NotFound, Unauthorized
from tastypie.authorization import Authorization


class UserObjectsOnlyAuthorization(Authorization):

    def _get_user(self, bundle):
        """Convenience method to extract current user from bundle."""

        return bundle.request.session.get("facility_user", None)

    def _user_is_admin(self, bundle):
        """Returns True if and only if the currently logged in user is an admin/teacher."""

        # allow central server superusers to do whatever they want
        if settings.CENTRAL_SERVER and bundle.request.user.is_superuser:
            return True

        # allow local admins (teachers or administrators) to do anything too
        if getattr(bundle.request, "is_admin", False):
            return True

    def _user_matches_query(self, bundle):
        """Returns True if and only if the user id in the query is the id of the currently logged in user."""

        user_actual = self._get_user(bundle)

        if not user_actual:
            return False

        user_queried = bundle.request.GET.get("user", None)

        if not user_queried:
            return False

        return user_actual.id == user_queried

    def _all_objects_belong_to_user(self, object_list, bundle):
        """Helper function that checks whether every object "belongs" to current user."""

        user = self._get_user(bundle)

        # Since they may not all be saved, iterate over them.
        for obj in object_list:
            if obj.user != user:
                return False

        return True

    def read_list(self, object_list, bundle):

        if _user_is_admin(bundle):
            return object_list

        if not self._user_matches_query(bundle):
            raise Unauthorized("Sorry, that information is restricted.")

        return object_list.filter(user=self._get_user(bundle))

    def read_detail(self, object_list, bundle):

        if _user_is_admin(bundle):
            return True

        return bundle.obj.user == self._get_user(bundle)

    def create_list(self, object_list, bundle):

        if _user_is_admin(bundle):
            return object_list

        if not self._all_objects_belong_to_user(object_list, bundle):
            raise Unauthorized("Sorry, that operation is restricted.")

        return object_list

    def create_detail(self, object_list, bundle):

        if _user_is_admin(bundle):
            return True

        return bundle.obj.user == self._get_user(bundle)

    def update_list(self, object_list, bundle):

        if _user_is_admin(bundle):
            return object_list

        if not self._all_objects_belong_to_user(object_list, bundle):
            raise Unauthorized("Sorry, that operation is restricted.")

        return object_list

    def update_detail(self, object_list, bundle):

        if _user_is_admin(bundle):
            return True

        if bundle.obj.user == self._get_user(bundle):
            return True

        raise Unauthorized("Sorry, that operation is restricted.")

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Sorry, that operation is restricted.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, that operation is restricted.")


def _user_is_admin(bundle):
    """Returns True if and only if the currently logged in user is an admin/teacher."""

    # allow central server superusers to do whatever they want
    if settings.CENTRAL_SERVER and bundle.request.user.is_superuser:
        return True

    # allow local admins (teachers or administrators) to do anything too
    if getattr(bundle.request, "is_admin", False):
        return True


class AdminReadWriteAndStudentReadOnlyAuthorization(Authorization):

    def _get_user(self, bundle):
        """Convenience method to extract current user from bundle."""

        return bundle.request.session.get("facility_user", None)

    def read_list(self, object_list, bundle):
        return object_list

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):

        if _user_is_admin(bundle):
            return object_list

        return []

    def create_detail(self, object_list, bundle):

        if _user_is_admin(bundle):
            return True

        raise Unauthorized("You are not allowed to access that resource.")

    def update_list(self, object_list, bundle):

        if _user_is_admin(bundle):
            return object_list

        return []

    def update_detail(self, object_list, bundle):

        import pdb; pdb.set_trace()

        if _user_is_admin(bundle):
            return True

        raise Unauthorized("You are not allowed to access that resource.")

    def delete_list(self, object_list, bundle):

        if _user_is_admin(bundle):
            return object_list

        return []

    def delete_detail(self, object_list, bundle):

        if _user_is_admin(bundle):
            return True

        raise Unauthorized(_("You are not allowed to access that resource."))


def tastypie_require_admin(handler):

    def require_admin_wrapper_fn(*args, **kwargs):

        bundle = kwargs.get("bundle", args[0])

        # TODO(jamalex): figure out how best to apply this on the central server once needed
        assert not settings.CENTRAL_SERVER

        if _user_is_admin(bundle):
            return handler(*args, **kwargs)

        raise Unauthorized(_("You do not have the permissions to access/modify this object."))

    return require_admin_wrapper_fn

