import { serverState } from "../../mock_server_state.hoot";
import { ServerModel } from "../mock_model";

export class ResUsers extends ServerModel {
    _name = "res.users";

    _records = [
        {
            id: serverState.userId,
            active: true,
            company_id: serverState.companyId,
            company_ids: [serverState.companyId],
            login: "admin",
            partner_id: serverState.partnerId,
            password: "admin",
        },
        {
            id: serverState.publicUserId,
            active: false,
            login: "public",
            partner_id: serverState.publicPartnerId,
            password: "public",
        },
    ];

    has_group() {
        return true;
    }
}
