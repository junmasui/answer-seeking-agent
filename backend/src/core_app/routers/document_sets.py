

from typing import Union, Annotated
import logging

from fastapi import Depends, APIRouter

from core import (list_document_sets)
from core.public_models import DocumentSetList


from simple_auth import User, get_scoped_current_user, Scope

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/', response_model=DocumentSetList)
async def handle_list_doc_sets(page: Union[int, None] = 0,
                            itemsPerPage: Union[int, None] = 10,
                            current_user: Annotated[User, Depends(
                                get_scoped_current_user(Scope.DOC_READ, missing_ok=True))] = None
                            ):
    """Returns a list of document sets.
    """

    return list_document_sets(start=page*itemsPerPage, length=itemsPerPage)
