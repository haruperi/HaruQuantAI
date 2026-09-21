import { Building2, Code2 } from 'lucide-react';
import { Button, Field, Section, Select, TextInput } from '../../components/ui';

export function BusinessWorkspace() {
  return (
    <div className="business">
      <div className="business-title">
        <Building2 size={25}/>
        <div>
          <h1>HaruQuantAI for Business</h1>
          <span>Team workspaces and compute administration</span>
        </div>
      </div>
      <div className="business-grid">
        <Section title="Workspace">
          <Field label="Organization">
            <TextInput defaultValue="Quant Research Lab"/>
          </Field>
          <Field label="Workspace">
            <Select value="Primary Research" onChange={() => {}}>
              <option>Primary Research</option>
              <option>Validation Team</option>
            </Select>
          </Field>
          <Field label="Default access">
            <Select value="Members can view" onChange={() => {}}>
              <option>Members can view</option>
              <option>Members can edit</option>
            </Select>
          </Field>
        </Section>
        <Section title="Compute nodes">
          <table className="mini-table">
            <tbody>
              <tr>
                <td>Local node</td>
                <td><span className="pill green">Online</span></td>
                <td>8 workers</td>
              </tr>
              <tr>
                <td>Research-02</td>
                <td><span className="pill">Mock</span></td>
                <td>16 workers</td>
              </tr>
            </tbody>
          </table>
          <p className="dialog-note">Remote workers are represented as fixtures; no network discovery occurs.</p>
        </Section>
        <Section title="MCP integration">
          <Field label="Server status">
            <TextInput value="Disabled (mock)" readOnly/>
          </Field>
          <Button>
            <Code2 size={14}/>Configure adapter
          </Button>
        </Section>
        <Section title="Users and roles">
          <table className="mini-table">
            <tbody>
              <tr>
                <td>Demo Administrator</td>
                <td>Owner</td>
                <td>Active</td>
              </tr>
              <tr>
                <td>Research Analyst</td>
                <td>Editor</td>
                <td>Fixture profile</td>
              </tr>
            </tbody>
          </table>
        </Section>
      </div>
    </div>
  );
}
export { BusinessWorkspace as Business };
